import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import redis
from sqlalchemy.orm import Session

from ai_service.config import AIConfig, PromptTemplates, InsightTypes, ChatContext
from db.models import AIInsight, Campaign
from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class InsightGenerator:
    """Core AI service for generating insights and handling chat"""
    
    def __init__(self, db: Session):
        self.db = db
        self.config = AIConfig()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
        # Configure OpenAI
        if self.config.OPENAI_API_KEY:
            openai.api_key = self.config.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
    
    def generate_campaign_insight(
        self,
        campaign_id: str,
        insight_type: str,
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insight for a campaign"""
        
        try:
            # Check cache first
            cache_key = self._get_cache_key(campaign_id, insight_type, context_data)
            cached_result = self._get_cached_insight(cache_key)
            if cached_result:
                return cached_result
            
            # Get campaign data
            campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise ValidationError("Campaign not found")
            
            # Generate prompt based on insight type
            prompt = self._build_insight_prompt(insight_type, context_data, campaign)
            
            # Call OpenAI
            response = self._call_openai(prompt)
            
            # Parse and structure the response
            insight_data = {
                "campaign_id": campaign_id,
                "insight_type": insight_type,
                "content": response,
                "generated_at": datetime.utcnow().isoformat(),
                "context_data": context_data
            }
            
            # Cache the result
            self._cache_insight(cache_key, insight_data)
            
            # Save to database
            self._save_insight_to_db(campaign_id, insight_type, response)
            
            return insight_data
            
        except Exception as e:
            logger.error(f"Failed to generate insight: {e}")
            raise ValidationError(f"Insight generation failed: {str(e)}")
    
    def generate_domain_insight(
        self,
        campaign_id: str,
        domain_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insight for a specific domain"""
        
        try:
            # Build domain analysis prompt
            prompt = PromptTemplates.DOMAIN_ANALYSIS_PROMPT.format(**domain_data)
            
            # Call OpenAI
            response = self._call_openai(prompt)
            
            return {
                "campaign_id": campaign_id,
                "domain": domain_data.get("domain"),
                "insight_type": InsightTypes.DOMAIN_INSIGHT,
                "content": response,
                "generated_at": datetime.utcnow().isoformat(),
                "domain_data": domain_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate domain insight: {e}")
            raise ValidationError(f"Domain insight generation failed: {str(e)}")
    
    def generate_whitelist_insight(
        self,
        campaign_id: str,
        whitelist_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insight for whitelist"""
        
        try:
            # Build whitelist analysis prompt
            prompt = PromptTemplates.WHITELIST_ANALYSIS_PROMPT.format(**whitelist_data)
            
            # Call OpenAI
            response = self._call_openai(prompt)
            
            return {
                "campaign_id": campaign_id,
                "insight_type": InsightTypes.WHITELIST_INSIGHT,
                "content": response,
                "generated_at": datetime.utcnow().isoformat(),
                "whitelist_data": whitelist_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate whitelist insight: {e}")
            raise ValidationError(f"Whitelist insight generation failed: {str(e)}")
    
    def generate_blacklist_insight(
        self,
        campaign_id: str,
        blacklist_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI insight for blacklist"""
        
        try:
            # Build blacklist analysis prompt
            prompt = PromptTemplates.BLACKLIST_ANALYSIS_PROMPT.format(**blacklist_data)
            
            # Call OpenAI
            response = self._call_openai(prompt)
            
            return {
                "campaign_id": campaign_id,
                "insight_type": InsightTypes.BLACKLIST_INSIGHT,
                "content": response,
                "generated_at": datetime.utcnow().isoformat(),
                "blacklist_data": blacklist_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate blacklist insight: {e}")
            raise ValidationError(f"Blacklist insight generation failed: {str(e)}")
    
    def chat_with_ai(
        self,
        user_id: str,
        message: str,
        campaign_id: Optional[str] = None,
        context: Optional[ChatContext] = None
    ) -> Dict[str, Any]:
        """Handle chat conversation with AI"""
        
        try:
            # Create or get chat context
            if not context:
                context = ChatContext(user_id, campaign_id)
            
            # Add user message to context
            context.add_message("user", message)
            
            # Build chat prompt
            chat_prompt = self._build_chat_prompt(message, context)
            
            # Call OpenAI
            response = self._call_openai(chat_prompt, system_prompt=PromptTemplates.CHAT_SYSTEM_PROMPT)
            
            # Add AI response to context
            context.add_message("assistant", response)
            
            return {
                "response": response,
                "conversation_id": self._get_conversation_id(user_id, campaign_id),
                "timestamp": datetime.utcnow().isoformat(),
                "context": context.get_context_summary()
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise ValidationError(f"Chat failed: {str(e)}")
    
    def _build_insight_prompt(
        self,
        insight_type: str,
        context_data: Dict[str, Any],
        campaign: Campaign
    ) -> str:
        """Build prompt for insight generation"""
        
        if insight_type == InsightTypes.PERFORMANCE_INSIGHT:
            return PromptTemplates.PERFORMANCE_INSIGHT_PROMPT.format(
                platform=campaign.campaign_type,
                goal=campaign.goal,
                channel=campaign.channel,
                **context_data
            )
        elif insight_type == InsightTypes.OPTIMIZATION_INSIGHT:
            return PromptTemplates.OPTIMIZATION_INSIGHT_PROMPT.format(
                platform=campaign.campaign_type,
                goal=campaign.goal,
                **context_data
            )
        elif insight_type == InsightTypes.CAMPAIGN_OVERVIEW:
            return PromptTemplates.CAMPAIGN_OVERVIEW_PROMPT.format(
                platform=campaign.campaign_type,
                goal=campaign.goal,
                channel=campaign.channel,
                **context_data
            )
        else:
            raise ValidationError(f"Unsupported insight type: {insight_type}")
    
    def _build_chat_prompt(self, message: str, context: ChatContext) -> str:
        """Build prompt for chat conversation"""
        
        # Get campaign context if available
        campaign_context = {}
        if context.campaign_id:
            campaign = self.db.query(Campaign).filter(Campaign.id == context.campaign_id).first()
            if campaign:
                campaign_context = {
                    "platform": campaign.campaign_type,
                    "goal": campaign.goal,
                    "channel": campaign.channel,
                    "current_score": "N/A"  # Would need to calculate from results
                }
        
        return PromptTemplates.CHAT_USER_PROMPT.format(
            user_question=message,
            **campaign_context
        )
    
    def _call_openai(self, prompt: str, system_prompt: str = None) -> str:
        """Call OpenAI API"""
        
        if not self.config.OPENAI_API_KEY:
            raise ValidationError("OpenAI API key not configured")
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = openai.ChatCompletion.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise ValidationError(f"AI service unavailable: {str(e)}")
    
    def _get_cache_key(self, campaign_id: str, insight_type: str, context_data: Dict[str, Any]) -> str:
        """Generate cache key for insight"""
        
        # Create a hash of the context data
        context_hash = hashlib.md5(
            json.dumps(context_data, sort_keys=True).encode()
        ).hexdigest()
        
        return f"insight:{campaign_id}:{insight_type}:{context_hash}"
    
    def _get_cached_insight(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached insight"""
        
        if not self.config.CACHE_ENABLED:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    def _cache_insight(self, cache_key: str, insight_data: Dict[str, Any]):
        """Cache insight data"""
        
        if not self.config.CACHE_ENABLED:
            return
        
        try:
            self.redis_client.setex(
                cache_key,
                self.config.CACHE_TTL,
                json.dumps(insight_data)
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _save_insight_to_db(self, campaign_id: str, insight_type: str, content: str):
        """Save insight to database"""
        
        try:
            insight = AIInsight(
                campaign_id=campaign_id,
                insight_type=insight_type,
                content=content
            )
            
            self.db.add(insight)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to save insight to database: {e}")
            # Don't raise - insight generation should still succeed
    
    def _get_conversation_id(self, user_id: str, campaign_id: Optional[str]) -> str:
        """Generate conversation ID"""
        
        if campaign_id:
            return f"{user_id}:{campaign_id}"
        else:
            return f"{user_id}:general"
    
    def get_campaign_insights(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get all insights for a campaign"""
        
        insights = self.db.query(AIInsight).filter(
            AIInsight.campaign_id == campaign_id
        ).order_by(AIInsight.created_at.desc()).all()
        
        return [
            {
                "id": insight.id,
                "insight_type": insight.insight_type,
                "content": insight.content,
                "created_at": insight.created_at.isoformat()
            }
            for insight in insights
        ]
    
    def delete_insight(self, insight_id: str):
        """Delete an insight"""
        
        insight = self.db.query(AIInsight).filter(AIInsight.id == insight_id).first()
        if insight:
            self.db.delete(insight)
            self.db.commit()
    
    def clear_campaign_insights(self, campaign_id: str):
        """Clear all insights for a campaign"""
        
        self.db.query(AIInsight).filter(AIInsight.campaign_id == campaign_id).delete()
        self.db.commit()

