"""
PDF generation utilities for reports
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def generate_summary_pdf(report_data: dict, output_path: str) -> str:
    """Generate a PDF summary report"""
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
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
    
    # Report information
    info_data = [
        ['Report ID:', report_data.get('id', 'N/A')],
        ['Filename:', report_data.get('filename', 'N/A')],
        ['Generated:', report_data.get('uploaded_at', 'N/A')],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    
    logger.info(f"Generated PDF: {output_path}")
    return output_path