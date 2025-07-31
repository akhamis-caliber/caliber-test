from typing import Dict, List, Any
import os
from datetime import datetime

class AIConfig:
    """Configuration for AI service"""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Cache Configuration
    CACHE_TTL = int(os.getenv("AI_CACHE_TTL", "3600"))  # 1 hour
    CACHE_ENABLED = os.getenv("AI_CACHE_ENABLED", "true").lower() == "true"
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = int(os.getenv("AI_MAX_REQUESTS_PER_MINUTE", "60"))
    MAX_REQUESTS_PER_HOUR = int(os.getenv("AI_MAX_REQUESTS_PER_HOUR", "1000"))

class PromptTemplates:
    """Templates for AI prompts"""
    
    # Campaign Analysis Prompts
    CAMPAIGN_OVERVIEW_PROMPT = """
    Analyze the following advertising campaign data and provide insights:
    
    Campaign Details:
    - Platform: {platform}
    - Goal: {goal}
    - Channel: {channel}
    - Total Domains: {total_domains}
    - Average Score: {average_score}
    
    Score Distribution:
    - Good: {good_count} domains
    - Moderate: {moderate_count} domains
    - Poor: {poor_count} domains
    
    Top Performers: {top_performers}
    Bottom Performers: {bottom_performers}
    
    Campaign Metrics:
    - Total Impressions: {total_impressions}
    - Total Spend: ${total_spend}
    - Average CPM: ${average_cpm}
    
    Data Quality Issues: {data_quality_issues}
    
    Please provide:
    1. Overall campaign performance assessment
    2. Key strengths and weaknesses
    3. Optimization recommendations
    4. Risk factors to consider
    5. Next steps for campaign improvement
    """
    
    DOMAIN_ANALYSIS_PROMPT = """
    Analyze the performance of the following domain in the advertising campaign:
    
    Domain: {domain}
    Score: {score}/100
    Quality Status: {quality_status}
    Percentile Rank: {percentile_rank}%
    
    Metrics:
    - Impressions: {impressions}
    - CTR: {ctr}%
    - CPM: ${cpm}
    - Conversions: {conversions}
    - Conversion Rate: {conversion_rate}%
    
    Score Breakdown: {score_breakdown}
    
    Please provide:
    1. Performance assessment for this domain
    2. Key factors contributing to the score
    3. Recommendations for improvement
    4. Whether to include in whitelist/blacklist
    """
    
    WHITELIST_ANALYSIS_PROMPT = """
    Analyze the whitelist generated for the campaign:
    
    Campaign: {campaign_name}
    Platform: {platform}
    Goal: {goal}
    
    Whitelist Details:
    - Number of domains: {domain_count}
    - Average score: {average_score}
    - Total impressions: {total_impressions}
    - Domains: {domains}
    
    Please provide:
    1. Assessment of whitelist quality
    2. Key characteristics of top performers
    3. Recommendations for whitelist usage
    4. Potential risks or considerations
    """
    
    BLACKLIST_ANALYSIS_PROMPT = """
    Analyze the blacklist generated for the campaign:
    
    Campaign: {campaign_name}
    Platform: {platform}
    Goal: {goal}
    
    Blacklist Details:
    - Number of domains: {domain_count}
    - Average score: {average_score}
    - Total impressions: {total_impressions}
    - Domains: {domains}
    
    Please provide:
    1. Assessment of blacklist quality
    2. Common issues with poor performers
    3. Recommendations for blacklist usage
    4. Potential false positives to consider
    """
    
    # Chat Prompts
    CHAT_SYSTEM_PROMPT = """
    You are an AI assistant for the Caliber advertising inventory scoring platform. 
    You help users understand their campaign performance and provide actionable insights.
    
    Your capabilities include:
    - Analyzing campaign performance data
    - Explaining scoring algorithms and metrics
    - Providing optimization recommendations
    - Interpreting whitelist and blacklist results
    - Answering questions about advertising metrics
    
    Always provide clear, actionable insights and explain technical concepts in simple terms.
    """
    
    CHAT_USER_PROMPT = """
    User Question: {user_question}
    
    Campaign Context (if available):
    - Platform: {platform}
    - Goal: {goal}
    - Channel: {channel}
    - Current Score: {current_score}
    
    Please provide a helpful, informative response that addresses the user's question.
    """
    
    # Insight Generation Prompts
    PERFORMANCE_INSIGHT_PROMPT = """
    Generate insights for the following campaign performance data:
    
    Campaign Summary:
    - Platform: {platform}
    - Goal: {goal}
    - Channel: {channel}
    - Overall Score: {overall_score}/100
    
    Performance Metrics:
    - Total Impressions: {total_impressions}
    - Average CTR: {average_ctr}%
    - Average CPM: ${average_cpm}
    - Conversion Rate: {conversion_rate}%
    
    Score Distribution:
    - Good: {good_percentage}%
    - Moderate: {moderate_percentage}%
    - Poor: {poor_percentage}%
    
    Top Issues: {top_issues}
    
    Generate 3-5 key insights that would be most valuable for the campaign manager.
    Focus on actionable recommendations and performance drivers.
    """
    
    OPTIMIZATION_INSIGHT_PROMPT = """
    Generate optimization recommendations for the campaign:
    
    Current Performance:
    - Overall Score: {overall_score}/100
    - Platform: {platform}
    - Goal: {goal}
    
    Key Metrics:
    - Average CTR: {average_ctr}%
    - Average CPM: ${average_cpm}
    - Conversion Rate: {conversion_rate}%
    
    Issues Identified: {issues}
    
    Available Actions:
    - Whitelist top performers
    - Blacklist poor performers
    - Adjust bidding strategies
    - Optimize targeting
    
    Provide 3-5 specific, actionable optimization recommendations.
    """

class InsightTypes:
    """Types of insights that can be generated"""
    
    PERFORMANCE_INSIGHT = "performance"
    OPTIMIZATION_INSIGHT = "optimization"
    WHITELIST_INSIGHT = "whitelist"
    BLACKLIST_INSIGHT = "blacklist"
    DOMAIN_INSIGHT = "domain"
    CAMPAIGN_OVERVIEW = "campaign_overview"
    
    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get all insight types"""
        return [
            cls.PERFORMANCE_INSIGHT,
            cls.OPTIMIZATION_INSIGHT,
            cls.WHITELIST_INSIGHT,
            cls.BLACKLIST_INSIGHT,
            cls.DOMAIN_INSIGHT,
            cls.CAMPAIGN_OVERVIEW
        ]

class ChatContext:
    """Context for chat conversations"""
    
    def __init__(self, user_id: str, campaign_id: str = None):
        self.user_id = user_id
        self.campaign_id = campaign_id
        self.conversation_history = []
        self.context_data = {}
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation context"""
        if not self.conversation_history:
            return ""
        
        # Get last few messages for context
        recent_messages = self.conversation_history[-5:]
        context = "Recent conversation:\n"
        
        for msg in recent_messages:
            context += f"{msg['role']}: {msg['content']}\n"
        
        return context
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = [] 