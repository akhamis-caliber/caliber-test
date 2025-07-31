from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import uuid
import logging
from datetime import datetime
import redis

from ai_service.insight_generator import InsightGenerator
from ai_service.config import AIConfig, ChatContext, InsightTypes
from db.models import Campaign, User, AIInsight
from common.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class AIController:
    """Controller for AI service operations"""
    
    @staticmethod
    def generate_campaign_insight(
        db: Session,
        campaign_id: uuid.UUID,
        insight_type: str,
        context_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Generate AI insight for a campaign"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Validate insight type
        if insight_type not in InsightTypes.get_all_types():
            raise ValidationError(f"Invalid insight type: {insight_type}")
        
        # Check rate limiting
        AIController._check_rate_limit(user.id)
        
        # Generate insight
        insight_generator = InsightGenerator(db)
        result = insight_generator.generate_campaign_insight(
            campaign_id=campaign_id,
            insight_type=insight_type,
            context_data=context_data
        )
        
        # Update rate limit
        AIController._update_rate_limit(user.id)
        
        return result
    
    @staticmethod
    def generate_domain_insight(
        db: Session,
        campaign_id: uuid.UUID,
        domain_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Generate AI insight for a specific domain"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Check rate limiting
        AIController._check_rate_limit(user.id)
        
        # Generate insight
        insight_generator = InsightGenerator(db)
        result = insight_generator.generate_domain_insight(
            campaign_id=campaign_id,
            domain_data=domain_data
        )
        
        # Update rate limit
        AIController._update_rate_limit(user.id)
        
        return result
    
    @staticmethod
    def generate_whitelist_insight(
        db: Session,
        campaign_id: uuid.UUID,
        whitelist_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Generate AI insight for whitelist"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Check rate limiting
        AIController._check_rate_limit(user.id)
        
        # Generate insight
        insight_generator = InsightGenerator(db)
        result = insight_generator.generate_whitelist_insight(
            campaign_id=campaign_id,
            whitelist_data=whitelist_data
        )
        
        # Update rate limit
        AIController._update_rate_limit(user.id)
        
        return result
    
    @staticmethod
    def generate_blacklist_insight(
        db: Session,
        campaign_id: uuid.UUID,
        blacklist_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Generate AI insight for blacklist"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Check rate limiting
        AIController._check_rate_limit(user.id)
        
        # Generate insight
        insight_generator = InsightGenerator(db)
        result = insight_generator.generate_blacklist_insight(
            campaign_id=campaign_id,
            blacklist_data=blacklist_data
        )
        
        # Update rate limit
        AIController._update_rate_limit(user.id)
        
        return result
    
    @staticmethod
    def generate_batch_insights(
        db: Session,
        campaign_id: uuid.UUID,
        insight_types: List[str],
        context_data: Dict[str, Any],
        user: User
    ) -> Dict[str, Any]:
        """Generate multiple insights for a campaign in batch"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Validate insight types
        valid_types = InsightTypes.get_all_types()
        invalid_types = [t for t in insight_types if t not in valid_types]
        if invalid_types:
            raise ValidationError(f"Invalid insight types: {invalid_types}")
        
        # Check rate limiting for batch operation
        AIController._check_rate_limit(user.id, multiplier=len(insight_types))
        
        insights = []
        failed_insights = []
        
        insight_generator = InsightGenerator(db)
        for insight_type in insight_types:
            try:
                result = insight_generator.generate_campaign_insight(
                    campaign_id=campaign_id,
                    insight_type=insight_type,
                    context_data=context_data
                )
                insights.append(result)
            except Exception as e:
                logger.error(f"Failed to generate {insight_type} insight: {e}")
                failed_insights.append(insight_type)
        
        # Update rate limit
        AIController._update_rate_limit(user.id, multiplier=len(insight_types))
        
        return {
            "campaign_id": campaign_id,
            "insights": insights,
            "generated_at": datetime.utcnow().isoformat(),
            "total_insights": len(insights),
            "failed_insights": failed_insights
        }
    
    @staticmethod
    def chat_with_ai(
        db: Session,
        user_id: str,
        message: str,
        campaign_id: Optional[uuid.UUID] = None,
        context_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Handle chat conversation with AI"""
        
        # Check rate limiting
        AIController._check_rate_limit(user_id)
        
        # Get or create chat context
        context = AIController._get_chat_context(user_id, campaign_id)
        
        # Generate response
        insight_generator = InsightGenerator(db)
        result = insight_generator.chat_with_ai(
            user_id=user_id,
            message=message,
            campaign_id=campaign_id,
            context=context
        )
        
        # Save chat context
        AIController._save_chat_context(context)
        
        # Update rate limit
        AIController._update_rate_limit(user_id)
        
        return result
    
    @staticmethod
    def get_campaign_insights(
        db: Session,
        campaign_id: uuid.UUID,
        insight_type: Optional[str] = None,
        user: User = None
    ) -> Dict[str, Any]:
        """Get all insights for a campaign"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Get insights from database
        query = db.query(AIInsight).filter(AIInsight.campaign_id == campaign_id)
        
        if insight_type:
            query = query.filter(AIInsight.insight_type == insight_type)
        
        insights = query.order_by(AIInsight.created_at.desc()).all()
        
        return {
            "campaign_id": campaign_id,
            "insights": [
                {
                    "id": insight.id,
                    "insight_type": insight.insight_type,
                    "content": insight.content,
                    "created_at": insight.created_at.isoformat()
                }
                for insight in insights
            ],
            "total_insights": len(insights),
            "insight_types": list(set(insight.insight_type for insight in insights))
        }
    
    @staticmethod
    def delete_insight(
        db: Session,
        insight_id: uuid.UUID,
        user: User
    ):
        """Delete an insight"""
        
        # Get insight and validate ownership
        insight = db.query(AIInsight).join(Campaign).filter(
            AIInsight.id == insight_id,
            Campaign.user_id == user.id
        ).first()
        
        if not insight:
            raise NotFoundError("Insight")
        
        # Delete from database
        insight_generator = InsightGenerator(db)
        insight_generator.delete_insight(insight_id)
        
        # Clear from cache
        AIController._clear_insight_cache(insight_id)
    
    @staticmethod
    def clear_campaign_insights(
        db: Session,
        campaign_id: uuid.UUID,
        user: User
    ):
        """Clear all insights for a campaign"""
        
        # Validate campaign ownership
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        # Clear from database
        insight_generator = InsightGenerator(db)
        insight_generator.clear_campaign_insights(campaign_id)
        
        # Clear from cache
        AIController._clear_campaign_cache(campaign_id)
    
    @staticmethod
    def get_chat_history(
        db: Session,
        conversation_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Get chat conversation history"""
        
        # Validate conversation ownership
        if not conversation_id.startswith(str(user.id)):
            raise NotFoundError("Conversation")
        
        # Get chat context from cache
        context = AIController._get_chat_context_from_cache(conversation_id)
        
        if not context:
            return {
                "conversation_id": conversation_id,
                "messages": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        
        return {
            "conversation_id": conversation_id,
            "messages": context.conversation_history,
            "created_at": context.context_data.get("created_at", datetime.utcnow().isoformat()),
            "updated_at": context.context_data.get("updated_at", datetime.utcnow().isoformat())
        }
    
    @staticmethod
    def clear_chat_history(
        db: Session,
        conversation_id: str,
        user: User
    ):
        """Clear chat conversation history"""
        
        # Validate conversation ownership
        if not conversation_id.startswith(str(user.id)):
            raise NotFoundError("Conversation")
        
        # Clear from cache
        AIController._clear_chat_context(conversation_id)
    
    @staticmethod
    def _check_rate_limit(user_id: str, multiplier: int = 1):
        """Check rate limiting for user"""
        
        config = AIConfig()
        redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
        minute_key = f"rate_limit:{user_id}:minute"
        hour_key = f"rate_limit:{user_id}:hour"
        
        # Check minute limit
        minute_count = redis_client.get(minute_key)
        if minute_count and int(minute_count) + multiplier > config.MAX_REQUESTS_PER_MINUTE:
            raise ValidationError("Rate limit exceeded for minute")
        
        # Check hour limit
        hour_count = redis_client.get(hour_key)
        if hour_count and int(hour_count) + multiplier > config.MAX_REQUESTS_PER_HOUR:
            raise ValidationError("Rate limit exceeded for hour")
    
    @staticmethod
    def _update_rate_limit(user_id: str, multiplier: int = 1):
        """Update rate limiting counters"""
        
        redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
        minute_key = f"rate_limit:{user_id}:minute"
        hour_key = f"rate_limit:{user_id}:hour"
        
        # Update minute counter
        redis_client.incrby(minute_key, multiplier)
        redis_client.expire(minute_key, 60)  # 1 minute
        
        # Update hour counter
        redis_client.incrby(hour_key, multiplier)
        redis_client.expire(hour_key, 3600)  # 1 hour
    
    @staticmethod
    def _get_chat_context(user_id: str, campaign_id: Optional[str]) -> ChatContext:
        """Get or create chat context"""
        
        conversation_id = f"{user_id}:{campaign_id}" if campaign_id else f"{user_id}:general"
        
        # Try to get from cache
        context = AIController._get_chat_context_from_cache(conversation_id)
        
        if not context:
            context = ChatContext(user_id, campaign_id)
            context.context_data = {
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        
        return context
    
    @staticmethod
    def _get_chat_context_from_cache(conversation_id: str) -> Optional[ChatContext]:
        """Get chat context from cache"""
        
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=1)
            cached_data = redis_client.get(f"chat_context:{conversation_id}")
            if cached_data:
                import json
                data = json.loads(cached_data)
                
                context = ChatContext(data["user_id"], data.get("campaign_id"))
                context.conversation_history = data["conversation_history"]
                context.context_data = data["context_data"]
                
                return context
        except Exception as e:
            logger.warning(f"Failed to get chat context from cache: {e}")
        
        return None
    
    @staticmethod
    def _save_chat_context(context: ChatContext):
        """Save chat context to cache"""
        
        try:
            conversation_id = f"{context.user_id}:{context.campaign_id}" if context.campaign_id else f"{context.user_id}:general"
            
            context.context_data["updated_at"] = datetime.utcnow().isoformat()
            
            data = {
                "user_id": context.user_id,
                "campaign_id": context.campaign_id,
                "conversation_history": context.conversation_history,
                "context_data": context.context_data
            }
            
            redis_client = redis.Redis(host='localhost', port=6379, db=1)
            redis_client.setex(
                f"chat_context:{conversation_id}",
                3600,  # 1 hour TTL
                json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Failed to save chat context to cache: {e}")
    
    @staticmethod
    def _clear_chat_context(conversation_id: str):
        """Clear chat context from cache"""
        
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=1)
            redis_client.delete(f"chat_context:{conversation_id}")
        except Exception as e:
            logger.warning(f"Failed to clear chat context from cache: {e}")
    
    @staticmethod
    def _clear_insight_cache(insight_id: str):
        """Clear insight from cache"""
        
        try:
            # This would need to be implemented based on cache key patterns
            # For now, we'll clear all insight cache for the campaign
            pass
        except Exception as e:
            logger.warning(f"Failed to clear insight cache: {e}")
    
    @staticmethod
    def _clear_campaign_cache(campaign_id: str):
        """Clear all cache for a campaign"""
        
        try:
            # Clear insight cache
            redis_client = redis.Redis(host='localhost', port=6379, db=1)
            pattern = f"insight:{campaign_id}:*"
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Failed to clear campaign cache: {e}")
    
    @staticmethod
    def get_ai_status() -> Dict[str, Any]:
        """Get AI service status"""
        
        config = AIConfig()
        return {
            "service_status": "operational" if config.OPENAI_API_KEY else "unconfigured",
            "openai_configured": bool(config.OPENAI_API_KEY),
            "cache_enabled": config.CACHE_ENABLED,
            "rate_limit_remaining": None,  # Would need to implement per-user tracking
            "last_request_time": None  # Would need to implement tracking
        } 