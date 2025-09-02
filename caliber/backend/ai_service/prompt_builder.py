"""
AI prompt builder for generating contextual prompts
"""

from typing import Dict, List, Any
import json


def build_insights_system_prompt() -> str:
    """Build system prompt for insights generation"""
    return """You are an expert digital advertising analyst specializing in campaign performance optimization. 
    
    Your role is to analyze campaign inventory data and provide actionable insights that help advertisers:
    - Identify top-performing domains, publishers, and supply sources
    - Understand performance patterns and trends
    - Make data-driven optimization decisions
    - Improve campaign ROI and efficiency
    
    Focus on practical, actionable insights rather than generic observations. Use the provided data to support your recommendations with specific metrics and comparisons."""


def build_insights_user_prompt(summary_data: Dict[str, Any], sample_rows: List[Dict]) -> str:
    """Build user prompt with report data for insights generation"""
    
    # Extract key metrics from summary
    total_rows = summary_data.get('total_rows', 0)
    score_distribution = summary_data.get('score_distribution', {})
    metrics_summary = summary_data.get('metrics_summary', {})
    
    # Format the prompt
    prompt = f"""Analyze this campaign performance data and provide actionable insights:

CAMPAIGN OVERVIEW:
- Total domains/publishers analyzed: {total_rows}
- Performance distribution: {json.dumps(score_distribution, indent=2)}

KEY METRICS SUMMARY:
{json.dumps(metrics_summary, indent=2)}

SAMPLE HIGH-PERFORMING DATA:
{json.dumps(sample_rows[:5], indent=2)}

Please provide:
1. 3-5 key insights about performance patterns
2. Specific recommendations for optimization
3. Identification of top opportunities and risks
4. Actionable next steps for campaign improvement

Keep insights concise but specific, with quantitative backing where possible."""
    
    return prompt


def build_chat_system_prompt() -> str:
    """Build system prompt for report chatbot"""
    return """You are a helpful assistant that answers questions about campaign performance data.

Guidelines:
- Only answer questions related to the specific report data provided
- Base responses on the actual data, not general knowledge
- Be concise and specific
- If asked about data not available in the report, clearly state that
- Focus on actionable information
- Use specific numbers and metrics when available"""


def build_chat_user_prompt(question: str, report_context: Dict[str, Any]) -> str:
    """Build user prompt for chat with report context"""
    
    prompt = f"""REPORT CONTEXT:
{json.dumps(report_context, indent=2)}

USER QUESTION: {question}

Please answer based on the report data provided above. If the question cannot be answered with the available data, explain what information would be needed."""
    
    return prompt


def build_explanation_prompt(domain: str, metrics: Dict[str, Any], score: float) -> str:
    """Build prompt for explaining individual domain scores"""
    
    prompt = f"""Explain why {domain} received a score of {score:.1f} based on these metrics:

Metrics:
- CPM: ${metrics.get('cpm', 'N/A')}
- CTR: {metrics.get('ctr', 'N/A')}%
- Conversion Rate: {metrics.get('conversion_rate', 'N/A')}%
- Total Spend: ${metrics.get('total_spend', 'N/A'):,}
- Impressions: {metrics.get('impressions', 'N/A'):,}

Provide a brief, clear explanation of the score in 1-2 sentences focusing on the key performance drivers."""
    
    return prompt