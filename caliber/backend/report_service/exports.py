"""
Report export functionality for CSV and PDF generation
"""

import pandas as pd
import io
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from db.models import Report, Campaign, ScoreRow
from config.settings import settings
from common.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)


class ReportExportController:
    def __init__(self, db: Session):
        self.db = db

    def export_csv(self, report_id: str, org_id: str) -> str:
        """Export all results as CSV string"""
        
        rows = self._get_score_rows(report_id, org_id)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'Domain': row.domain,
                'Publisher': row.publisher or '',
                'CPM': row.cpm or 0,
                'CTR': row.ctr or 0,
                'Conversion_Rate': row.conversion_rate or 0,
                'Impressions': row.impressions or 0,
                'Total_Spend': row.total_spend or 0,
                'Conversions': row.conversions or 0,
                'Score': row.score,
                'Status': row.status.value,
                'Channel': row.channel or '',
                'Vendor': row.vendor or '',
                'Explanation': row.explanation or ''
            }
            for row in rows
        ])
        
        return df.to_csv(index=False)

    def export_whitelist_csv(self, report_id: str, org_id: str) -> str:
        """Export top 25% performers as CSV"""
        
        rows = self._get_score_rows(report_id, org_id)
        
        # Get top 25%
        sorted_rows = sorted(rows, key=lambda x: x.score, reverse=True)
        top_25_percent = int(len(sorted_rows) * 0.25)
        whitelist_rows = sorted_rows[:top_25_percent]
        
        df = pd.DataFrame([
            {
                'Domain': row.domain,
                'Publisher': row.publisher or '',
                'Score': row.score,
                'Status': row.status.value,
                'CPM': row.cpm or 0,
                'CTR': row.ctr or 0,
                'Conversion_Rate': row.conversion_rate or 0
            }
            for row in whitelist_rows
        ])
        
        return df.to_csv(index=False)

    def export_blacklist_csv(self, report_id: str, org_id: str) -> str:
        """Export bottom 25% performers as CSV"""
        
        rows = self._get_score_rows(report_id, org_id)
        
        # Get bottom 25%
        sorted_rows = sorted(rows, key=lambda x: x.score)
        bottom_25_percent = int(len(sorted_rows) * 0.25)
        blacklist_rows = sorted_rows[:bottom_25_percent]
        
        df = pd.DataFrame([
            {
                'Domain': row.domain,
                'Publisher': row.publisher or '',
                'Score': row.score,
                'Status': row.status.value,
                'CPM': row.cpm or 0,
                'CTR': row.ctr or 0,
                'Conversion_Rate': row.conversion_rate or 0
            }
            for row in blacklist_rows
        ])
        
        return df.to_csv(index=False)

    def export_pdf(self, report_id: str, org_id: str) -> str:
        """Export summary report as PDF and return file path"""
        
        report = self._get_report(report_id, org_id)
        rows = self._get_score_rows(report_id, org_id)
        
        # Create output directory
        output_dir = Path(settings.STORAGE_ROOT) / str(org_id) / str(report_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        pdf_path = output_dir / f"summary_{report_id}.pdf"
        
        # Create PDF
        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#2563eb')
        )
        
        # Title
        story.append(Paragraph("Caliber Campaign Performance Report", title_style))
        story.append(Spacer(1, 12))
        
        # Report Info
        report_info = [
            ['Report:', report.filename],
            ['Campaign:', report.campaign.name if hasattr(report, 'campaign') else 'N/A'],
            ['Generated:', report.uploaded_at.strftime('%Y-%m-%d %H:%M')],
            ['Total Domains:', str(len(rows))]
        ]
        
        info_table = Table(report_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Summary Statistics
        if report.summary_json:
            summary = report.summary_json
            
            story.append(Paragraph("Performance Summary", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Domains', str(summary.get('total_rows', 0))],
                ['Good Performance', str(summary.get('score_distribution', {}).get('Good', 0))],
                ['Average CPM', f"${summary.get('metrics_summary', {}).get('cpm', {}).get('mean', 0):.2f}"],
                ['Average CTR', f"{summary.get('metrics_summary', {}).get('ctr', {}).get('mean', 0)*100:.2f}%"],
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 20))
        
        # Top Performers
        story.append(Paragraph("Top 10 Performers", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        top_rows = sorted(rows, key=lambda x: x.score, reverse=True)[:10]
        
        top_data = [['Domain', 'Score', 'Status', 'CPM', 'CTR']]
        for row in top_rows:
            top_data.append([
                row.domain[:30] + '...' if len(row.domain) > 30 else row.domain,
                f"{row.score:.1f}",
                row.status.value,
                f"${row.cmp:.2f}" if row.cpm else 'N/A',
                f"{row.ctr*100:.2f}%" if row.ctr else 'N/A'
            ])
        
        top_table = Table(top_data, colWidths=[2.5*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#22c55e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
        ]))
        
        story.append(top_table)
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"Generated PDF report: {pdf_path}")
        return str(pdf_path)

    def _get_report(self, report_id: str, org_id: str) -> Report:
        """Get report with validation"""
        
        report = self.db.query(Report).join(Campaign).filter(
            Report.id == report_id,
            Campaign.org_id == org_id
        ).first()
        
        if not report:
            raise NotFoundError("Report not found")
        
        return report

    def _get_score_rows(self, report_id: str, org_id: str) -> List[ScoreRow]:
        """Get all score rows for a report"""
        
        # Validate report exists and belongs to org
        self._get_report(report_id, org_id)
        
        rows = self.db.query(ScoreRow).filter(
            ScoreRow.report_id == report_id
        ).all()
        
        return rows