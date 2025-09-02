"""
AI chatbot for interactive Q&A about campaign data
"""

import openai
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from db.models import Report, Campaign
from ai_service.prompt_builder import build_chat_system_prompt, build_chat_user_prompt
from common.exceptions import NotFoundError
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class ReportChatbot:
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "replace_me":
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai

    async def chat(self, chat_request: Any, org_id: str) -> Dict[str, Any]:
        """Handle chat request about report data"""
        
        report_id = str(chat_request.report_id)
        message = chat_request.message
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Get report and validate
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        try:
            if self.client and report.summary_json:
                # Use AI to generate response
                response_text = await self._generate_ai_response(
                    message, report.summary_json, report_id
                )
            else:
                # Fallback to deterministic response
                response_text = self._generate_deterministic_response(
                    message, report.summary_json if report.summary_json else {}
                )
        
        except Exception as e:
            logger.error(f"Failed to generate chat response: {str(e)}")
            response_text = self._generate_error_response()
        
        return {
            "message": response_text,
            "report_id": report_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": None  # Could include specific data sources used
        }

    async def _generate_ai_response(
        self, question: str, report_context: Dict, report_id: str
    ) -> str:
        """Generate response using OpenAI"""
        
        system_prompt = build_chat_system_prompt()
        user_prompt = build_chat_user_prompt(question, report_context)
        
        try:
            response = await self.client.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI chat API call failed: {str(e)}")
            return self._generate_deterministic_response(question, report_context)

    def _generate_deterministic_response(self, question: str, context: Dict) -> str:
        """Generate response using rule-based logic"""
        
        question_lower = question.lower()
        
        # Performance questions
        if any(word in question_lower for word in ['performance', 'score', 'good', 'bad']):
            return self._answer_performance_question(context)
        
        # Cost questions
        elif any(word in question_lower for word in ['cost', 'cpm', 'spend', 'expensive']):
            return self._answer_cost_question(context)
        
        # CTR questions
        elif any(word in question_lower for word in ['ctr', 'click', 'engagement']):
            return self._answer_ctr_question(context)
        
        # Conversion questions
        elif any(word in question_lower for word in ['conversion', 'convert', 'action']):
            return self._answer_conversion_question(context)
        
        # Top performer questions
        elif any(word in question_lower for word in ['top', 'best', 'highest']):
            return self._answer_top_performer_question(context)
        
        # General questions
        elif any(word in question_lower for word in ['total', 'how many', 'overview']):
            return self._answer_general_question(context)
        
        else:
            return self._generate_default_response()

    def _answer_performance_question(self, context: Dict) -> str:
        """Answer questions about performance"""
        
        score_dist = context.get('score_distribution', {})
        total_rows = context.get('total_rows', 0)
        
        if not score_dist or total_rows == 0:
            return "I don't have enough performance data to answer that question."
        
        good_count = score_dist.get('Good', 0)
        moderate_count = score_dist.get('Moderate', 0)
        poor_count = score_dist.get('Poor', 0)
        
        good_pct = (good_count / total_rows * 100) if total_rows > 0 else 0
        
        return f"Your campaign has {good_count} domains with 'Good' performance ({good_pct:.1f}%), " \
               f"{moderate_count} with 'Moderate' performance, and {poor_count} with 'Poor' performance. " \
               f"This gives you a solid foundation to optimize around the top performers."

    def _answer_cost_question(self, context: Dict) -> str:
        """Answer questions about costs and CPM"""
        
        metrics = context.get('metrics_summary', {})
        cpm_stats = metrics.get('cpm', {})
        
        if not cpm_stats:
            return "I don't have CPM data available for this report."
        
        avg_cpm = cpm_stats.get('mean', 0)
        min_cpm = cpm_stats.get('min', 0)
        max_cpm = cpm_stats.get('max', 0)
        
        if avg_cpm > 0:
            return f"Your average CPM is ${avg_cpm:.2f}, ranging from ${min_cpm:.2f} to ${max_cpm:.2f}. " \
                   f"{'This is quite efficient!' if avg_cmp < 3 else 'There may be opportunities to reduce costs by focusing on lower-CPM inventory.'}"
        
        return "CPM data is not available in this report."

    def _answer_ctr_question(self, context: Dict) -> str:
        """Answer questions about CTR and engagement"""
        
        metrics = context.get('metrics_summary', {})
        ctr_stats = metrics.get('ctr', {})
        
        if not ctr_stats:
            return "I don't have CTR data available for this report."
        
        avg_ctr = ctr_stats.get('mean', 0) * 100
        
        if avg_ctr > 0:
            performance_level = "excellent" if avg_ctr > 2 else "good" if avg_ctr > 1 else "below average"
            return f"Your average CTR is {avg_ctr:.2f}%, which is {performance_level} for digital advertising. " \
                   f"{'Keep up the great work!' if avg_ctr > 1.5 else 'Consider testing different creative approaches to improve engagement.'}"
        
        return "CTR data is not available in this report."

    def _answer_conversion_question(self, context: Dict) -> str:
        """Answer questions about conversions"""
        
        metrics = context.get('metrics_summary', {})
        conv_stats = metrics.get('conversion_rate', {})
        
        if not conv_stats:
            return "I don't have conversion data available for this report."
        
        avg_conv = conv_stats.get('mean', 0) * 100
        
        if avg_conv > 0:
            return f"Your average conversion rate is {avg_conv:.2f}%. " \
                   f"This varies significantly by industry, but focus on domains with above-average conversion rates for better ROI."
        
        return "Conversion rate data is not available in this report."

    def _answer_top_performer_question(self, context: Dict) -> str:
        """Answer questions about top performers"""
        
        top_domains = context.get('top_domains', [])
        
        if not top_domains:
            return "I don't have top performer data available."
        
        top_domain = top_domains[0]
        return f"Your top performing domain is {top_domain.get('domain', 'N/A')} with a score of " \
               f"{top_domain.get('score', 0):.1f}. Consider allocating more budget to similar high-performing inventory."

    def _answer_general_question(self, context: Dict) -> str:
        """Answer general questions about the campaign"""
        
        total_rows = context.get('total_rows', 0)
        score_dist = context.get('score_distribution', {})
        
        if total_rows == 0:
            return "This report doesn't contain any scored data yet."
        
        return f"This campaign analyzed {total_rows} domains. " \
               f"Performance breakdown: {score_dist.get('Good', 0)} Good, " \
               f"{score_dist.get('Moderate', 0)} Moderate, {score_dist.get('Poor', 0)} Poor. " \
               f"You can use the data table and export features to dive deeper into the results."

    def _generate_default_response(self) -> str:
        """Generate default response for unrecognized questions"""
        
        return "I can help you understand your campaign performance data. Try asking about:\n" \
               "• Overall performance or scores\n" \
               "• Cost efficiency (CPM)\n" \
               "• Click-through rates (CTR)\n" \
               "• Top performing domains\n" \
               "• Conversion rates\n\n" \
               "What would you like to know?"

    def _generate_error_response(self) -> str:
        """Generate response for errors"""
        
        return "I'm sorry, I encountered an issue processing your question. " \
               "Please try rephrasing or ask about specific metrics like performance scores, costs, or top domains."