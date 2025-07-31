import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ai_service.config import PromptTemplates, InsightTypes
from db.models import Campaign

logger = logging.getLogger(__name__)

class PromptBuilder:
    """Builder for creating AI prompts for different types of insights"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_campaign_insight_prompt(
        self,
        insight_type: str,
        campaign: Campaign,
        context_data: Dict[str, Any]
    ) -> str:
        """Build a prompt for campaign insights"""
        
        base_prompt = self._get_base_campaign_prompt(campaign)
        
        if insight_type == InsightTypes.PERFORMANCE:
            return self._build_performance_prompt(base_prompt, context_data)
        elif insight_type == InsightTypes.OPTIMIZATION:
            return self._build_optimization_prompt(base_prompt, context_data)
        elif insight_type == InsightTypes.WHITELIST:
            return self._build_whitelist_prompt(base_prompt, context_data)
        elif insight_type == InsightTypes.BLACKLIST:
            return self._build_blacklist_prompt(base_prompt, context_data)
        elif insight_type == InsightTypes.CAMPAIGN_OVERVIEW:
            return self._build_overview_prompt(base_prompt, context_data)
        else:
            return self._build_generic_prompt(base_prompt, insight_type, context_data)
    
    def build_domain_analysis_prompt(
        self,
        domain_data: Dict[str, Any],
        campaign: Optional[Campaign] = None
    ) -> str:
        """Build a prompt for domain analysis"""
        
        prompt = f"""
        Analyze the following domain performance data for digital advertising:

        Domain: {domain_data.get('domain', 'Unknown')}
        Impressions: {domain_data.get('impressions', 0):,}
        Clicks: {domain_data.get('clicks', 0):,}
        CTR: {domain_data.get('ctr', 0):.2%}
        Conversions: {domain_data.get('conversions', 0):,}
        Conversion Rate: {domain_data.get('conversion_rate', 0):.2%}
        Cost: ${domain_data.get('cost', 0):,.2f}
        Revenue: ${domain_data.get('revenue', 0):,.2f}
        ROAS: {domain_data.get('roas', 0):.2f}
        
        Additional Context:
        - Quality Score: {domain_data.get('quality_score', 'N/A')}
        - Brand Safety: {domain_data.get('brand_safety', 'N/A')}
        - Content Categories: {domain_data.get('content_categories', 'N/A')}
        
        Please provide:
        1. Performance assessment (good/moderate/poor)
        2. Key strengths and weaknesses
        3. Recommendations for optimization
        4. Risk assessment
        5. Whether this domain should be whitelisted or blacklisted
        """
        
        if campaign:
            prompt += f"\n\nCampaign Context:\n- Type: {campaign.campaign_type}\n- Goal: {campaign.goal}\n- Channel: {campaign.channel}"
        
        return prompt
    
    def build_whitelist_analysis_prompt(
        self,
        whitelist_data: Dict[str, Any],
        campaign: Optional[Campaign] = None
    ) -> str:
        """Build a prompt for whitelist analysis"""
        
        domains = whitelist_data.get('domains', [])
        top_domains = domains[:10] if len(domains) > 10 else domains
        
        prompt = f"""
        Analyze the following whitelist of top-performing domains:

        Total Domains: {len(domains)}
        Top Domains:
        {self._format_domain_list(top_domains)}
        
        Performance Summary:
        - Average CTR: {whitelist_data.get('avg_ctr', 0):.2%}
        - Average Conversion Rate: {whitelist_data.get('avg_conversion_rate', 0):.2%}
        - Average ROAS: {whitelist_data.get('avg_roas', 0):.2f}
        - Total Impressions: {whitelist_data.get('total_impressions', 0):,}
        - Total Revenue: ${whitelist_data.get('total_revenue', 0):,.2f}
        
        Please provide:
        1. Analysis of common characteristics among top performers
        2. Patterns in content categories or domains
        3. Recommendations for expanding the whitelist
        4. Potential risks or considerations
        5. Optimization strategies for these domains
        """
        
        if campaign:
            prompt += f"\n\nCampaign Context:\n- Type: {campaign.campaign_type}\n- Goal: {campaign.goal}\n- Channel: {campaign.channel}"
        
        return prompt
    
    def build_blacklist_analysis_prompt(
        self,
        blacklist_data: Dict[str, Any],
        campaign: Optional[Campaign] = None
    ) -> str:
        """Build a prompt for blacklist analysis"""
        
        domains = blacklist_data.get('domains', [])
        top_domains = domains[:10] if len(domains) > 10 else domains
        
        prompt = f"""
        Analyze the following blacklist of poor-performing domains:

        Total Domains: {len(domains)}
        Top Poor Performers:
        {self._format_domain_list(top_domains)}
        
        Performance Summary:
        - Average CTR: {blacklist_data.get('avg_ctr', 0):.2%}
        - Average Conversion Rate: {blacklist_data.get('avg_conversion_rate', 0):.2%}
        - Average ROAS: {blacklist_data.get('avg_roas', 0):.2f}
        - Total Impressions: {blacklist_data.get('total_impressions', 0):,}
        - Total Cost: ${blacklist_data.get('total_cost', 0):,.2f}
        
        Please provide:
        1. Analysis of common characteristics among poor performers
        2. Patterns in content categories or domains
        3. Recommendations for avoiding similar domains
        4. Potential brand safety concerns
        5. Strategies for improving performance
        """
        
        if campaign:
            prompt += f"\n\nCampaign Context:\n- Type: {campaign.campaign_type}\n- Goal: {campaign.goal}\n- Channel: {campaign.channel}"
        
        return prompt
    
    def build_chat_prompt(
        self,
        message: str,
        context_data: Dict[str, Any],
        campaign: Optional[Campaign] = None
    ) -> str:
        """Build a prompt for chat interactions"""
        
        prompt = f"""
        You are Caliber, an AI assistant specialized in digital advertising and campaign optimization.
        
        User Message: {message}
        
        Context Information:
        {json.dumps(context_data, indent=2)}
        """
        
        if campaign:
            prompt += f"""
            
            Campaign Information:
            - Name: {campaign.name}
            - Type: {campaign.campaign_type}
            - Goal: {campaign.goal}
            - Channel: {campaign.channel}
            - Status: {campaign.status}
            """
        
        prompt += """
        
        Please provide a helpful, professional response that:
        1. Addresses the user's question or concern
        2. Provides actionable advice when possible
        3. Uses campaign context to give relevant insights
        4. Maintains a professional and helpful tone
        """
        
        return prompt
    
    def _get_base_campaign_prompt(self, campaign: Campaign) -> str:
        """Get the base campaign information for prompts"""
        
        return f"""
        Campaign Information:
        - Name: {campaign.name}
        - Type: {campaign.campaign_type}
        - Goal: {campaign.goal}
        - Channel: {campaign.channel}
        - CTR Sensitivity: {campaign.ctr_sensitivity}
        - Analysis Level: {campaign.analysis_level}
        - Status: {campaign.status}
        - Created: {campaign.created_at}
        """
    
    def _build_performance_prompt(self, base_prompt: str, context_data: Dict[str, Any]) -> str:
        """Build performance analysis prompt"""
        
        return f"""
        {base_prompt}
        
        Analyze the performance of this digital advertising campaign and provide insights on:
        
        1. Overall Performance Assessment
        2. Key Performance Indicators (KPIs)
        3. Performance Trends
        4. Comparative Analysis
        5. Performance Drivers
        6. Areas of Concern
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide a comprehensive performance analysis with actionable insights.
        """
    
    def _build_optimization_prompt(self, base_prompt: str, context_data: Dict[str, Any]) -> str:
        """Build optimization recommendations prompt"""
        
        return f"""
        {base_prompt}
        
        Provide optimization recommendations for this digital advertising campaign:
        
        1. Targeting Optimization
        2. Creative Optimization
        3. Bidding Strategy
        4. Budget Allocation
        5. Performance Monitoring
        6. A/B Testing Recommendations
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide specific, actionable optimization recommendations.
        """
    
    def _build_whitelist_prompt(self, base_prompt: str, context_data: Dict[str, Any]) -> str:
        """Build whitelist analysis prompt"""
        
        return f"""
        {base_prompt}
        
        Analyze the whitelist data for this campaign:
        
        1. Top Performing Domains
        2. Common Characteristics
        3. Expansion Opportunities
        4. Risk Assessment
        5. Implementation Strategy
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide insights on the whitelist and recommendations for optimization.
        """
    
    def _build_blacklist_prompt(self, base_prompt: str, context_data: Dict[str, Any]) -> str:
        """Build blacklist analysis prompt"""
        
        return f"""
        {base_prompt}
        
        Analyze the blacklist data for this campaign:
        
        1. Poor Performing Domains
        2. Common Characteristics
        3. Risk Factors
        4. Avoidance Strategies
        5. Monitoring Recommendations
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide insights on the blacklist and recommendations for risk mitigation.
        """
    
    def _build_overview_prompt(self, base_prompt: str, context_data: Dict[str, Any]) -> str:
        """Build campaign overview prompt"""
        
        return f"""
        {base_prompt}
        
        Provide a comprehensive overview of this digital advertising campaign:
        
        1. Campaign Summary
        2. Performance Overview
        3. Key Insights
        4. Recommendations
        5. Next Steps
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide a comprehensive campaign overview with actionable insights.
        """
    
    def _build_generic_prompt(self, base_prompt: str, insight_type: str, context_data: Dict[str, Any]) -> str:
        """Build a generic prompt for unknown insight types"""
        
        return f"""
        {base_prompt}
        
        Provide insights for {insight_type} analysis:
        
        Context Data:
        {json.dumps(context_data, indent=2)}
        
        Please provide relevant insights and recommendations based on the available data.
        """
    
    def _format_domain_list(self, domains: List[Dict[str, Any]]) -> str:
        """Format a list of domains for display in prompts"""
        
        if not domains:
            return "No domains available"
        
        formatted = []
        for i, domain in enumerate(domains[:10], 1):
            domain_info = f"{i}. {domain.get('domain', 'Unknown')}"
            if 'impressions' in domain:
                domain_info += f" ({domain['impressions']:,} impressions)"
            if 'ctr' in domain:
                domain_info += f" - CTR: {domain['ctr']:.2%}"
            formatted.append(domain_info)
        
        return "\n".join(formatted)

