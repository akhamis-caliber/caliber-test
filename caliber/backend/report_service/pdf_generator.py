from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
import io
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from db.models import Campaign, ScoringResult, User
from scoring_service.controllers import ScoringController
from common.exceptions import ValidationError, NotFoundError

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generate comprehensive PDF reports for campaigns"""
    
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.darkblue
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading3'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.darkgreen
        ))
        
        # Metric style
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
            alignment=TA_LEFT
        ))
        
        # Summary style
        self.styles.add(ParagraphStyle(
            name='Summary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            alignment=TA_LEFT,
            leftIndent=20
        ))
    
    def generate_campaign_report(
        self,
        campaign_id: str,
        user: User,
        include_charts: bool = True,
        include_details: bool = True
    ) -> bytes:
        """Generate comprehensive campaign report PDF"""
        
        # Validate campaign ownership
        campaign = self.db.query(Campaign).filter(
            Campaign.id == campaign_id,
            Campaign.user_id == user.id
        ).first()
        
        if not campaign:
            raise NotFoundError("Campaign")
        
        if campaign.status != "completed":
            raise ValidationError("Campaign scoring not completed")
        
        # Create PDF document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Add title page
        story.extend(self._create_title_page(campaign))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(campaign))
        story.append(PageBreak())
        
        # Add campaign overview
        story.extend(self._create_campaign_overview(campaign))
        
        # Add performance metrics
        story.extend(self._create_performance_metrics(campaign))
        
        # Add charts if requested
        if include_charts:
            story.extend(self._create_charts(campaign))
        
        # Add detailed results if requested
        if include_details:
            story.extend(self._create_detailed_results(campaign))
        
        # Add optimization recommendations
        story.extend(self._create_optimization_recommendations(campaign))
        
        # Add appendix
        story.extend(self._create_appendix(campaign))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer.getvalue()
    
    def _create_title_page(self, campaign: Campaign) -> List:
        """Create title page"""
        
        story = []
        
        # Title
        title = Paragraph(f"Campaign Report: {campaign.name}", self.styles['CustomTitle'])
        story.append(title)
        story.append(Spacer(1, 2*inch))
        
        # Campaign details table
        campaign_data = [
            ["Campaign Name:", campaign.name],
            ["Platform:", campaign.campaign_type],
            ["Goal:", campaign.goal],
            ["Channel:", campaign.channel],
            ["Status:", campaign.status],
            ["Created:", campaign.created_at.strftime("%B %d, %Y")],
            ["Report Generated:", datetime.utcnow().strftime("%B %d, %Y at %I:%M %p")]
        ]
        
        campaign_table = Table(campaign_data, colWidths=[2*inch, 4*inch])
        campaign_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(campaign_table)
        
        return story
    
    def _create_executive_summary(self, campaign: Campaign) -> List:
        """Create executive summary section"""
        
        story = []
        
        # Section header
        story.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get campaign summary data
        summary_data = ScoringController.get_campaign_summary(
            db=self.db,
            campaign_id=campaign.id,
            user=campaign.user
        )
        
        # Overall performance
        overall_score = summary_data["average_score"]
        total_domains = summary_data["total_domains"]
        good_domains = summary_data["score_distribution"]["good"]
        poor_domains = summary_data["score_distribution"]["poor"]
        
        # Performance assessment
        if overall_score >= 80:
            performance_level = "Excellent"
            performance_color = colors.darkgreen
        elif overall_score >= 60:
            performance_level = "Good"
            performance_color = colors.blue
        elif overall_score >= 40:
            performance_level = "Moderate"
            performance_color = colors.orange
        else:
            performance_level = "Poor"
            performance_color = colors.red
        
        # Create performance summary
        performance_text = f"""
        <b>Overall Performance:</b> {performance_level} ({overall_score:.1f}/100)<br/>
        <b>Total Domains Analyzed:</b> {total_domains:,}<br/>
        <b>High-Quality Domains:</b> {good_domains} ({good_domains/total_domains*100:.1f}%)<br/>
        <b>Low-Quality Domains:</b> {poor_domains} ({poor_domains/total_domains*100:.1f}%)<br/>
        """
        
        performance_para = Paragraph(performance_text, self.styles['Summary'])
        story.append(performance_para)
        story.append(Spacer(1, 12))
        
        # Key insights
        story.append(Paragraph("Key Insights:", self.styles['SubsectionHeader']))
        
        insights = []
        if good_domains > poor_domains:
            insights.append("• Campaign shows strong inventory quality with more high-performing domains than low-performing ones")
        else:
            insights.append("• Campaign has optimization opportunities with more low-performing domains than high-performing ones")
        
        if overall_score >= 70:
            insights.append("• Overall inventory quality is above industry standards")
        elif overall_score < 50:
            insights.append("• Overall inventory quality needs significant improvement")
        
        insights.append(f"• {good_domains} domains qualify for whitelist optimization")
        insights.append(f"• {poor_domains} domains should be considered for blacklist")
        
        for insight in insights:
            story.append(Paragraph(insight, self.styles['Summary']))
        
        return story
    
    def _create_campaign_overview(self, campaign: Campaign) -> List:
        """Create campaign overview section"""
        
        story = []
        
        story.append(Paragraph("Campaign Overview", self.styles['SectionHeader']))
        
        # Campaign metrics
        summary_data = ScoringController.get_campaign_summary(
            db=self.db,
            campaign_id=campaign.id,
            user=campaign.user
        )
        
        metrics_data = [
            ["Metric", "Value"],
            ["Total Impressions", f"{summary_data['campaign_metrics']['total_impressions']:,}"],
            ["Total Spend", f"${summary_data['campaign_metrics']['total_spend']:,.2f}"],
            ["Average CPM", f"${summary_data['campaign_metrics']['average_cpm']:.2f}"],
            ["Campaign Score", f"{summary_data['campaign_metrics']['campaign_level_score']:.1f}/100"],
            ["Total Domains", f"{summary_data['total_domains']:,}"],
            ["Processing Date", campaign.completed_at.strftime("%B %d, %Y") if campaign.completed_at else "N/A"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.5*inch, 2.5*inch])
        metrics_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_performance_metrics(self, campaign: Campaign) -> List:
        """Create performance metrics section"""
        
        story = []
        
        story.append(Paragraph("Performance Metrics", self.styles['SectionHeader']))
        
        # Get scoring results for metrics
        results_data = ScoringController.get_scoring_results(
            db=self.db,
            campaign_id=campaign.id,
            user=campaign.user,
            page=1,
            per_page=1000
        )
        
        if not results_data["results"]:
            return story
        
        # Calculate metrics
        scores = [r["score"] for r in results_data["results"]]
        impressions = [r["impressions"] for r in results_data["results"]]
        ctrs = [r["ctr"] for r in results_data["results"]]
        cpms = [r["cpm"] for r in results_data["results"]]
        
        # Score distribution
        score_dist = {
            "Excellent (80-100)": len([s for s in scores if s >= 80]),
            "Good (60-79)": len([s for s in scores if 60 <= s < 80]),
            "Moderate (40-59)": len([s for s in scores if 40 <= s < 60]),
            "Poor (0-39)": len([s for s in scores if s < 40])
        }
        
        # Create metrics table
        metrics_data = [
            ["Metric", "Value", "Description"],
            ["Average Score", f"{sum(scores)/len(scores):.1f}", "Overall inventory quality score"],
            ["Median Score", f"{sorted(scores)[len(scores)//2]:.1f}", "Middle score value"],
            ["Score Range", f"{min(scores)} - {max(scores)}", "Lowest to highest score"],
            ["Average CTR", f"{sum(ctrs)/len(ctrs):.4f}%", "Average click-through rate"],
            ["Average CPM", f"${sum(cpms)/len(cpms):.2f}", "Average cost per thousand impressions"],
            ["Total Volume", f"{sum(impressions):,}", "Total impression volume"]
        ]
        
        metrics_table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        metrics_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (2, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _create_charts(self, campaign: Campaign) -> List:
        """Create charts and visualizations"""
        
        story = []
        
        story.append(Paragraph("Performance Visualizations", self.styles['SectionHeader']))
        
        # Get data for charts
        results_data = ScoringController.get_scoring_results(
            db=self.db,
            campaign_id=campaign.id,
            user=campaign.user,
            page=1,
            per_page=1000
        )
        
        if not results_data["results"]:
            return story
        
        # Score distribution pie chart
        story.append(Paragraph("Score Distribution", self.styles['SubsectionHeader']))
        
        scores = [r["score"] for r in results_data["results"]]
        score_dist = {
            "Excellent (80-100)": len([s for s in scores if s >= 80]),
            "Good (60-79)": len([s for s in scores if 60 <= s < 80]),
            "Moderate (40-59)": len([s for s in scores if 40 <= s < 60]),
            "Poor (0-39)": len([s for s in scores if s < 40])
        }
        
        # Create pie chart
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 100
        pie.height = 100
        pie.data = list(score_dist.values())
        pie.labels = list(score_dist.keys())
        pie.slices.strokeWidth = 0.5
        
        drawing.add(pie)
        story.append(drawing)
        story.append(Spacer(1, 20))
        
        # Top performers table
        story.append(Paragraph("Top 10 Performing Domains", self.styles['SubsectionHeader']))
        
        top_performers = sorted(results_data["results"], key=lambda x: x["score"], reverse=True)[:10]
        
        top_data = [["Rank", "Domain", "Score", "Impressions", "CTR", "CPM"]]
        for i, result in enumerate(top_performers, 1):
            top_data.append([
                str(i),
                result["domain"][:30] + "..." if len(result["domain"]) > 30 else result["domain"],
                str(result["score"]),
                f"{result['impressions']:,}",
                f"{result['ctr']:.4f}%",
                f"${result['cpm']:.2f}"
            ])
        
        top_table = Table(top_data, colWidths=[0.5*inch, 2*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch])
        top_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        story.append(top_table)
        story.append(PageBreak())
        
        return story
    
    def _create_detailed_results(self, campaign: Campaign) -> List:
        """Create detailed results section"""
        
        story = []
        
        story.append(Paragraph("Detailed Results", self.styles['SectionHeader']))
        
        # Get all results
        results_data = ScoringController.get_scoring_results(
            db=self.db,
            campaign_id=campaign.id,
            user=campaign.user,
            page=1,
            per_page=1000
        )
        
        if not results_data["results"]:
            return story
        
        # Create results table (first 50 results)
        results = results_data["results"][:50]
        
        results_data_table = [["Domain", "Score", "Status", "Impressions", "CTR", "CPM"]]
        for result in results:
            results_data_table.append([
                result["domain"][:25] + "..." if len(result["domain"]) > 25 else result["domain"],
                str(result["score"]),
                result["quality_status"],
                f"{result['impressions']:,}",
                f"{result['ctr']:.4f}%",
                f"${result['cpm']:.2f}"
            ])
        
        results_table = Table(results_data_table, colWidths=[2*inch, 0.8*inch, 1*inch, 1*inch, 0.8*inch, 0.8*inch])
        results_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ]))
        
        story.append(results_table)
        
        if len(results_data["results"]) > 50:
            story.append(Paragraph(f"<i>Showing first 50 of {len(results_data['results'])} results</i>", self.styles['Summary']))
        
        story.append(PageBreak())
        
        return story
    
    def _create_optimization_recommendations(self, campaign: Campaign) -> List:
        """Create optimization recommendations section"""
        
        story = []
        
        story.append(Paragraph("Optimization Recommendations", self.styles['SectionHeader']))
        
        # Get whitelist and blacklist
        try:
            whitelist_data = ScoringController.generate_optimization_list(
                db=self.db,
                campaign_id=campaign.id,
                user=campaign.user,
                list_type="whitelist",
                min_impressions=250
            )
            
            blacklist_data = ScoringController.generate_optimization_list(
                db=self.db,
                campaign_id=campaign.id,
                user=campaign.user,
                list_type="blacklist",
                min_impressions=250
            )
            
            # Whitelist recommendations
            story.append(Paragraph("Whitelist Recommendations", self.styles['SubsectionHeader']))
            whitelist_text = f"""
            <b>Recommended Domains:</b> {len(whitelist_data['domains'])} domains<br/>
            <b>Average Score:</b> {whitelist_data['average_score']:.1f}/100<br/>
            <b>Total Impressions:</b> {whitelist_data['total_impressions']:,}<br/>
            <b>Action:</b> Increase bidding and targeting for these high-performing domains
            """
            story.append(Paragraph(whitelist_text, self.styles['Summary']))
            
            # Blacklist recommendations
            story.append(Paragraph("Blacklist Recommendations", self.styles['SubsectionHeader']))
            blacklist_text = f"""
            <b>Domains to Avoid:</b> {len(blacklist_data['domains'])} domains<br/>
            <b>Average Score:</b> {blacklist_data['average_score']:.1f}/100<br/>
            <b>Total Impressions:</b> {blacklist_data['total_impressions']:,}<br/>
            <b>Action:</b> Exclude these low-performing domains from future campaigns
            """
            story.append(Paragraph(blacklist_text, self.styles['Summary']))
            
        except Exception as e:
            story.append(Paragraph("Unable to generate optimization lists", self.styles['Summary']))
        
        # General recommendations
        story.append(Paragraph("General Recommendations", self.styles['SubsectionHeader']))
        
        recommendations = [
            "• Monitor performance regularly and adjust bidding strategies based on domain performance",
            "• Consider implementing dynamic bidding for high-performing domains",
            "• Review and update whitelist/blacklist monthly based on new performance data",
            "• Focus on domains with consistent performance over time",
            "• Consider expanding to similar domains that show promise"
        ]
        
        for rec in recommendations:
            story.append(Paragraph(rec, self.styles['Summary']))
        
        return story
    
    def _create_appendix(self, campaign: Campaign) -> List:
        """Create appendix section"""
        
        story = []
        
        story.append(Paragraph("Appendix", self.styles['SectionHeader']))
        
        # Scoring methodology
        story.append(Paragraph("Scoring Methodology", self.styles['SubsectionHeader']))
        methodology_text = """
        The inventory quality score is calculated using a weighted combination of key performance metrics:
        <br/><br/>
        • <b>Click-Through Rate (CTR):</b> Measures user engagement and ad effectiveness<br/>
        • <b>Cost Per Mille (CPM):</b> Indicates cost efficiency and inventory quality<br/>
        • <b>Conversion Rate:</b> Measures campaign effectiveness for action-based goals<br/>
        • <b>Volume:</b> Ensures sufficient data for reliable scoring<br/>
        <br/>
        Scores are normalized to a 0-100 scale where higher scores indicate better performance.
        """
        story.append(Paragraph(methodology_text, self.styles['Summary']))
        
        # Data quality notes
        if campaign.data_quality_report:
            story.append(Paragraph("Data Quality Notes", self.styles['SubsectionHeader']))
            quality_text = f"""
            Data quality assessment completed during processing:<br/>
            • {campaign.data_quality_report.get('total_records', 0)} total records processed<br/>
            • {len(campaign.data_quality_report.get('data_quality_issues', []))} quality issues identified<br/>
            • Processing completed on {campaign.completed_at.strftime('%B %d, %Y') if campaign.completed_at else 'N/A'}
            """
            story.append(Paragraph(quality_text, self.styles['Summary']))
        
        return story

