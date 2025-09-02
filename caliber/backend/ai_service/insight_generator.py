"""
AI-powered insight generation for campaign reports
"""

import openai
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from datetime import datetime

from db.models import Report, Campaign, ScoreRow
from ai_service.prompt_builder import build_insights_system_prompt, build_insights_user_prompt
from common.exceptions import NotFoundError
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class InsightGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.client = None
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "replace_me":
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai

    async def generate_insights(self, report_id: str, org_id: str) -> Dict[str, Any]:
        """Generate AI insights for a report"""
        
        # Get report and validate
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        if not report.summary_json:
            # Return deterministic insights if no summary available
            return self._generate_fallback_insights(report_id)
        
        # Get sample high-performing rows
        sample_rows = self.db.query(ScoreRow).filter(
            ScoreRow.report_id == report_id
        ).order_by(ScoreRow.score.desc()).limit(10).all()
        
        sample_data = [
            {
                'domain': row.domain,
                'score': row.score,
                'status': row.status.value,
                'cpm': row.cpm,
                'ctr': row.ctr,
                'conversion_rate': row.conversion_rate
            }
            for row in sample_rows
        ]
        
        try:
            if self.client:
                # Use AI to generate insights
                return await self._generate_ai_insights(report.summary_json, sample_data, report_id)
            else:
                # Fallback to deterministic insights
                return self._generate_deterministic_insights(report.summary_json, sample_data, report_id)
        
        except Exception as e:
            logger.error(f"Failed to generate AI insights: {str(e)}")
            return self._generate_fallback_insights(report_id)

    async def _generate_ai_insights(
        self, summary_data: Dict, sample_rows: List[Dict], report_id: str
    ) -> Dict[str, Any]:
        """Generate insights using OpenAI"""
        
        system_prompt = build_insights_system_prompt()
        user_prompt = build_insights_user_prompt(summary_data, sample_rows)
        
        try:
            response = await self.client.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            insights_text = response.choices[0].message.content
            
            # Parse insights into structured format
            key_findings = self._extract_key_findings(insights_text)
            recommendations = self._extract_recommendations(insights_text)
            
            return {
                "report_id": report_id,
                "insights_text": insights_text,
                "key_findings": key_findings,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            return self._generate_deterministic_insights(summary_data, sample_rows, report_id)

    def _generate_deterministic_insights(
        self, summary_data: Dict, sample_rows: List[Dict], report_id: str
    ) -> Dict[str, Any]:
        """Generate insights using deterministic logic"""
        
        total_rows = summary_data.get('total_rows', 0)
        score_dist = summary_data.get('score_distribution', {})
        metrics = summary_data.get('metrics_summary', {})
        
        key_findings = []
        recommendations = []
        
        # Performance distribution analysis
        good_count = score_dist.get('Good', 0)
        good_percentage = (good_count / total_rows * 100) if total_rows > 0 else 0
        
        if good_percentage > 30:
            key_findings.append(f"Strong portfolio performance with {good_percentage:.1f}% of domains achieving 'Good' scores")
        elif good_percentage > 15:
            key_findings.append(f"Moderate performance with {good_percentage:.1f}% of domains in 'Good' category")
        else:
            key_findings.append(f"Performance opportunities identified - only {good_percentage:.1f}% of domains rated 'Good'")
        
        # CPM analysis
        avg_cpm = metrics.get('cpm', {}).get('mean', 0)
        if avg_cpm > 0:
            if avg_cpm < 2:
                key_findings.append(f"Efficient cost structure with average CPM of ${avg_cpm:.2f}")
            elif avg_cpm < 5:
                key_findings.append(f"Moderate CPM efficiency at ${avg_cpm:.2f} average")
            else:
                key_findings.append(f"High CPM of ${avg_cpm:.2f} suggests cost optimization opportunities")
                recommendations.append("Focus on lower-cost inventory sources to improve efficiency")
        
        # CTR analysis
        avg_ctr = metrics.get('ctr', {}).get('mean', 0)
        if avg_ctr > 0:
            ctr_percent = avg_ctr * 100
            if ctr_percent > 2:
                key_findings.append(f"Excellent engagement with {ctr_percent:.2f}% average CTR")
            elif ctr_percent > 1:
                key_findings.append(f"Good engagement levels at {ctr_percent:.2f}% CTR")
            else:
                key_findings.append(f"CTR of {ctr_percent:.2f}% indicates room for creative optimization")
                recommendations.append("Consider A/B testing creative assets to improve click-through rates")
        
        # Top performer insights
        if sample_rows:
            top_domain = sample_rows[0]
            key_findings.append(f"Top performer {top_domain['domain']} achieved {top_domain['score']:.1f} score")
            
            # Identify patterns in top performers
            top_5 = sample_rows[:5]
            avg_top_cpm = sum(row.get('cpm', 0) for row in top_5 if row.get('cpm')) / len(top_5)
            if avg_top_cpm > 0:
                recommendations.append(f"Top performers average ${avg_top_cpm:.2f} CPM - target similar inventory")
        
        # General recommendations
        poor_count = score_dist.get('Poor', 0)
        if poor_count > total_rows * 0.25:  # More than 25% poor
            recommendations.append("Consider blacklisting bottom 25% of domains to improve campaign efficiency")
        
        recommendations.append("Focus budget allocation on 'Good' and 'Moderate' performing inventory")
        
        insights_text = self._format_insights_text(key_findings, recommendations)
        
        return {
            "report_id": report_id,
            "insights_text": insights_text,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _generate_fallback_insights(self, report_id: str) -> Dict[str, Any]:
        """Generate basic fallback insights when data is limited"""
        
        key_findings = [
            "Campaign data has been processed and scored",
            "Performance analysis is available in the data table",
            "Domains have been categorized by performance level"
        ]
        
        recommendations = [
            "Review the detailed score breakdown in the data table",
            "Use export functions to create whitelist and blacklist files",
            "Monitor top-performing domains for future campaigns"
        ]
        
        insights_text = self._format_insights_text(key_findings, recommendations)
        
        return {
            "report_id": report_id,
            "insights_text": insights_text,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _extract_key_findings(self, text: str) -> List[str]:
        """Extract key findings from AI-generated text"""
        # Simple extraction logic - in production, use more sophisticated parsing
        lines = text.split('\n')
        findings = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                findings.append(line[1:].strip())
            elif any(keyword in line.lower() for keyword in ['finding', 'shows', 'indicates', 'reveals']):
                findings.append(line)
        
        return findings[:5]  # Limit to 5 findings

    def _extract_recommendations(self, text: str) -> List[str]:
        """Extract recommendations from AI-generated text"""
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider', 'optimize']):
                recommendations.append(line)
        
        return recommendations[:5]  # Limit to 5 recommendations

    def _format_insights_text(self, key_findings: List[str], recommendations: List[str]) -> str:
        """Format insights into readable text"""
        
        text_parts = ["## Key Performance Insights\n"]
        
        for i, finding in enumerate(key_findings, 1):
            text_parts.append(f"{i}. {finding}")
        
        text_parts.append("\n## Recommendations\n")
        
        for i, rec in enumerate(recommendations, 1):
            text_parts.append(f"{i}. {rec}")
        
        return "\n".join(text_parts)