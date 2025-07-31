import openai
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import redis

from ai_service.config import AIConfig, ChatContext
from common.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ChatBot:
    """AI ChatBot for handling conversations with users"""
    
    def __init__(self):
        self.config = AIConfig()
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)
        
        # Configure OpenAI
        if self.config.OPENAI_API_KEY:
            openai.api_key = self.config.OPENAI_API_KEY
        else:
            logger.warning("OpenAI API key not configured")
    
    def generate_response(
        self,
        message: str,
        context: ChatContext,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a response to a user message"""
        
        try:
            # Build the conversation history
            messages = self._build_messages(message, context, system_prompt)
            
            # Call OpenAI
            response = self._call_openai(messages)
            
            # Update context
            context.add_message("user", message)
            context.add_message("assistant", response)
            
            return {
                "response": response,
                "conversation_id": context.conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context.get_summary()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate chat response: {e}")
            raise ValidationError(f"Chat failed: {str(e)}")
    
    def _build_messages(
        self,
        message: str,
        context: ChatContext,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build the messages array for OpenAI API"""
        
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # Default system prompt
            default_prompt = """You are Caliber, an AI assistant specialized in digital advertising and campaign optimization. 
            You help users analyze campaign performance, provide insights, and suggest optimizations.
            Be helpful, professional, and provide actionable advice."""
            messages.append({"role": "system", "content": default_prompt})
        
        # Add conversation history (limit to last 10 messages to avoid token limits)
        history = context.get_recent_messages(10)
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        return messages
    
    def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API to generate response"""
        
        if not self.config.OPENAI_API_KEY:
            raise ValidationError("OpenAI API key not configured")
        
        try:
            response = openai.ChatCompletion.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P,
                frequency_penalty=self.config.FREQUENCY_PENALTY,
                presence_penalty=self.config.PRESENCE_PENALTY
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise ValidationError(f"AI service unavailable: {str(e)}")
    
    def get_conversation_summary(self, context: ChatContext) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        
        return {
            "conversation_id": context.conversation_id,
            "total_messages": len(context.conversation_history),
            "created_at": context.context_data.get("created_at"),
            "updated_at": context.context_data.get("updated_at"),
            "summary": context.get_summary()
        }
    
    def clear_conversation(self, context: ChatContext) -> bool:
        """Clear the conversation history"""
        
        try:
            context.clear_history()
            return True
        except Exception as e:
            logger.error(f"Failed to clear conversation: {e}")
            return False
    
    def save_conversation(self, context: ChatContext) -> bool:
        """Save conversation to cache"""
        
        try:
            conversation_id = context.conversation_id
            data = {
                "conversation_history": context.conversation_history,
                "context_data": context.context_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                f"chat:{conversation_id}",
                3600,  # 1 hour TTL
                json.dumps(data)
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> Optional[ChatContext]:
        """Load conversation from cache"""
        
        try:
            cached_data = self.redis_client.get(f"chat:{conversation_id}")
            if cached_data:
                data = json.loads(cached_data)
                
                # Create new context
                context = ChatContext(
                    user_id=data.get("user_id"),
                    campaign_id=data.get("campaign_id")
                )
                context.conversation_history = data.get("conversation_history", [])
                context.context_data = data.get("context_data", {})
                
                return context
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
        
        return None

