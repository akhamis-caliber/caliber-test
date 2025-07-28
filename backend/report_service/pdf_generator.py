import os
import json
import io
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    Image, PageBreak, KeepTogether, Frame, PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import seaborn as sns
import pandas as pd
import base64

class PDFGenerator:
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = template_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.custom_styles = {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#1f2937'),
                fontName='Helvetica-Bold'
            ),
            'Subtitle': ParagraphStyle(
                'CustomSubtitle',
                parent=self.styles['Heading2'],
                fontSize=18,
                spaceAfter=20,
                textColor=colors.HexColor('#374151'),
                fontName='Helvetica-Bold'
            ),
            'Heading': ParagraphStyle(
                'CustomHeading',
                parent=self.styles['Heading3'],
                fontSize=14,
                spaceAfter=15,
                textColor=colors.HexColor('#4b5563'),
                fontName='Helvetica-Bold'
            ),
            'Body': ParagraphStyle(
                'CustomBody',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=8,
                textColor=colors.HexColor('#6b7280'),
                fontName='Helvetica'
            ),
            'Highlight': ParagraphStyle(
                'CustomHighlight',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                textColor=colors.HexColor('#059669'),
                fontName='Helvetica-Bold'
            ),
            'Warning': ParagraphStyle(
                'CustomWarning',
                parent=self.styles['Normal'],
                fontSize=11,
                spaceAfter=8,
                textColor=colors.HexColor('#dc2626'),
                fontName='Helvetica-Bold'
            )
        }

    def generate_report(self, 
                       data: List[Dict[str, Any]], 
                       report_config: Dict[str, Any],
                       branding_config: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Generate a comprehensive PDF report
        
        Args:
            data: Report data
            report_config: Report configuration
            branding_config: Custom branding configuration
            
        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        
        # Setup branding
        branding = self._setup_branding(branding_config)
        
        # Create document with custom page template
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1.5*inch,
            bottomMargin=1*inch
        )
        
        # Create page template with header/footer
        page_template = self._create_page_template(branding)
        doc.addPageTemplates([page_template])
        
        # Build story
        story = []
        
        # Add cover page
        story.extend(self._create_cover_page(report_config, branding))
        story.append(PageBreak())
        
        # Add table of contents
        story.extend(self._create_table_of_contents(report_config))
        story.append(PageBreak())
        
        # Add executive summary
        story.extend(self._create_executive_summary(data, report_config))
        story.append(PageBreak())
        
        # Add detailed analysis
        story.extend(self._create_detailed_analysis(data, report_config))
        story.append(PageBreak())
        
        # Add charts and visualizations
        story.extend(self._create_charts_section(data, report_config))
        story.append(PageBreak())
        
        # Add insights and recommendations
        story.extend(self._create_insights_section(data, report_config))
        story.append(PageBreak())
        
        # Add appendix
        story.extend(self._create_appendix(data, report_config))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    def _setup_branding(self, branding_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Setup branding configuration"""
        default_branding = {
            'company_name': 'Caliber Scoring System',
            'company_logo': None,
            'primary_color': '#3B82F6',
            'secondary_color': '#1F2937',
            'accent_color': '#10B981',
            'font_family': 'Helvetica',
            'header_text': 'Caliber Scoring Report',
            'footer_text': 'Generated by Caliber Scoring System'
        }
        
        if branding_config:
            default_branding.update(branding_config)
            
        return default_branding

    def _create_page_template(self, branding: Dict[str, Any]):
        """Create page template with header and footer"""
        def header_footer(canvas, doc):
            # Header
            canvas.saveState()
            canvas.setFont(branding['font_family'], 10)
            canvas.setFillColor(colors.HexColor(branding['primary_color']))
            canvas.drawString(doc.leftMargin, doc.height + doc.topMargin + 0.5*inch, 
                            branding['header_text'])
            
            # Footer
            canvas.setFont(branding['font_family'], 8)
            canvas.setFillColor(colors.HexColor(branding['secondary_color']))
            canvas.drawString(doc.leftMargin, 0.5*inch, branding['footer_text'])
            
            # Page number
            canvas.drawRightString(doc.width + doc.leftMargin, 0.5*inch, 
                                 f"Page {doc.page}")
            canvas.restoreState()
        
        return PageTemplate(id='custom', frames=[Frame(
            doc.leftMargin, doc.bottomMargin, doc.width, doc.height, 
            id='normal'
        )], onPage=header_footer)

    def _create_cover_page(self, report_config: Dict[str, Any], 
                          branding: Dict[str, Any]) -> List:
        """Create cover page"""
        elements = []
        
        # Title
        elements.append(Paragraph(
            report_config.get('title', 'Scoring Report'), 
            self.custom_styles['Title']
        ))
        elements.append(Spacer(1, 40))
        
        # Subtitle
        if report_config.get('subtitle'):
            elements.append(Paragraph(
                report_config['subtitle'], 
                self.custom_styles['Subtitle']
            ))
            elements.append(Spacer(1, 30))
        
        # Generation info
        elements.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", 
            self.custom_styles['Body']
        ))
        elements.append(Spacer(1, 20))
        
        # Company info
        elements.append(Paragraph(
            f"Prepared by: {branding['company_name']}", 
            self.custom_styles['Body']
        ))
        elements.append(Spacer(1, 40))
        
        # Report metadata
        if report_config.get('metadata'):
            metadata_table = self._create_metadata_table(report_config['metadata'])
            elements.append(metadata_table)
        
        return elements

    def _create_table_of_contents(self, report_config: Dict[str, Any]) -> List:
        """Create table of contents"""
        elements = []
        
        elements.append(Paragraph("Table of Contents", self.custom_styles['Title']))
        elements.append(Spacer(1, 30))
        
        sections = [
            "Executive Summary",
            "Detailed Analysis", 
            "Charts and Visualizations",
            "Insights and Recommendations",
            "Appendix"
        ]
        
        for i, section in enumerate(sections, 1):
            elements.append(Paragraph(
                f"{i}. {section}", 
                self.custom_styles['Body']
            ))
            elements.append(Spacer(1, 10))
        
        return elements

    def _create_executive_summary(self, data: List[Dict[str, Any]], 
                                 report_config: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.custom_styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Key metrics summary
        if data:
            summary_stats = self._calculate_summary_statistics(data)
            
            # Create summary table
            summary_data = [
                ['Metric', 'Value', 'Status'],
                ['Total Records', str(len(data)), '✓'],
                ['Average Score', f"{summary_stats['avg_score']:.2f}", 
                 self._get_score_status(summary_stats['avg_score'])],
                ['Highest Score', f"{summary_stats['max_score']:.2f}", '✓'],
                ['Lowest Score', f"{summary_stats['min_score']:.2f}", '⚠'],
                ['Score Range', f"{summary_stats['score_range']:.2f}", '✓']
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch, 1*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
        
        # Executive summary text
        summary_text = report_config.get('executive_summary', 
            "This report provides a comprehensive analysis of the scoring results. "
            "The data has been processed and analyzed to provide actionable insights "
            "for campaign optimization and performance improvement.")
        
        elements.append(Paragraph(summary_text, self.custom_styles['Body']))
        
        return elements

    def _create_detailed_analysis(self, data: List[Dict[str, Any]], 
                                 report_config: Dict[str, Any]) -> List:
        """Create detailed analysis section"""
        elements = []
        
        elements.append(Paragraph("Detailed Analysis", self.custom_styles['Title']))
        elements.append(Spacer(1, 20))
        
        if not data:
            elements.append(Paragraph(
                "No data available for detailed analysis.", 
                self.custom_styles['Body']
            ))
            return elements
        
        # Performance breakdown
        elements.append(Paragraph("Performance Breakdown", self.custom_styles['Heading']))
        elements.append(Spacer(1, 10))
        
        # Create detailed results table
        if data:
            headers = list(data[0].keys())
            table_data = [headers]  # Header row
            
            for row in data:
                table_data.append([str(row.get(header, '')) for header in headers])
            
            # Limit rows to prevent table from being too large
            if len(table_data) > 50:
                table_data = table_data[:50]
                table_data.append(['...', '...', '...', '...', '...'])
            
            results_table = Table(table_data, colWidths=[1.2*inch] * len(headers))
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')])
            ]))
            
            elements.append(results_table)
        
        return elements

    def _create_charts_section(self, data: List[Dict[str, Any]], 
                              report_config: Dict[str, Any]) -> List:
        """Create charts and visualizations section"""
        elements = []
        
        elements.append(Paragraph("Charts and Visualizations", self.custom_styles['Title']))
        elements.append(Spacer(1, 20))
        
        if not data:
            elements.append(Paragraph(
                "No data available for charts.", 
                self.custom_styles['Body']
            ))
            return elements
        
        # Generate charts
        charts = self._generate_charts(data)
        
        for chart in charts:
            elements.append(Paragraph(chart['title'], self.custom_styles['Heading']))
            elements.append(Spacer(1, 10))
            
            if chart['image']:
                # Convert base64 to image
                img_data = base64.b64decode(chart['image'])
                img_buffer = io.BytesIO(img_data)
                
                # Add image to PDF
                img = Image(img_buffer, width=6*inch, height=4*inch)
                elements.append(img)
                elements.append(Spacer(1, 15))
            
            if chart['description']:
                elements.append(Paragraph(chart['description'], self.custom_styles['Body']))
                elements.append(Spacer(1, 20))
        
        return elements

    def _create_insights_section(self, data: List[Dict[str, Any]], 
                                report_config: Dict[str, Any]) -> List:
        """Create insights and recommendations section"""
        elements = []
        
        elements.append(Paragraph("Insights and Recommendations", self.custom_styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Generate insights
        insights = self._generate_insights(data)
        
        elements.append(Paragraph("Key Insights", self.custom_styles['Heading']))
        elements.append(Spacer(1, 10))
        
        for i, insight in enumerate(insights, 1):
            elements.append(Paragraph(
                f"{i}. {insight}", 
                self.custom_styles['Body']
            ))
            elements.append(Spacer(1, 5))
        
        elements.append(Spacer(1, 20))
        
        # Recommendations
        recommendations = self._generate_recommendations(data)
        
        elements.append(Paragraph("Recommendations", self.custom_styles['Heading']))
        elements.append(Spacer(1, 10))
        
        for i, rec in enumerate(recommendations, 1):
            elements.append(Paragraph(
                f"{i}. {rec}", 
                self.custom_styles['Highlight']
            ))
            elements.append(Spacer(1, 5))
        
        return elements

    def _create_appendix(self, data: List[Dict[str, Any]], 
                        report_config: Dict[str, Any]) -> List:
        """Create appendix section"""
        elements = []
        
        elements.append(Paragraph("Appendix", self.custom_styles['Title']))
        elements.append(Spacer(1, 20))
        
        # Data dictionary
        elements.append(Paragraph("Data Dictionary", self.custom_styles['Heading']))
        elements.append(Spacer(1, 10))
        
        if data:
            # Create data dictionary table
            field_descriptions = self._get_field_descriptions(data[0])
            dict_data = [['Field', 'Type', 'Description']]
            
            for field, desc in field_descriptions.items():
                field_type = type(data[0].get(field, '')).__name__
                dict_data.append([field, field_type, desc])
            
            dict_table = Table(dict_data, colWidths=[1.5*inch, 1*inch, 3*inch])
            dict_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            elements.append(dict_table)
        
        return elements

    def _create_metadata_table(self, metadata: Dict[str, Any]) -> Table:
        """Create metadata table"""
        data = [['Property', 'Value']]
        for key, value in metadata.items():
            data.append([key, str(value)])
        
        table = Table(data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f9fafb')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        return table

    def _calculate_summary_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate summary statistics from data"""
        scores = []
        for item in data:
            score = item.get('score')
            if score is not None and isinstance(score, (int, float)):
                scores.append(float(score))
        
        if not scores:
            return {
                'avg_score': 0.0,
                'max_score': 0.0,
                'min_score': 0.0,
                'score_range': 0.0
            }
        
        return {
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'score_range': max(scores) - min(scores)
        }

    def _get_score_status(self, score: float) -> str:
        """Get status indicator for score"""
        if score >= 80:
            return '✓'
        elif score >= 60:
            return '⚠'
        else:
            return '✗'

    def _generate_charts(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate charts from data"""
        charts = []
        
        if not data:
            return charts
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Score distribution chart
        if 'score' in df.columns:
            chart1 = self._create_score_distribution_chart(df)
            charts.append(chart1)
        
        # Performance trend chart (if date column exists)
        date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
        if date_columns and 'score' in df.columns:
            chart2 = self._create_performance_trend_chart(df, date_columns[0])
            charts.append(chart2)
        
        # Metric comparison chart
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 1:
            chart3 = self._create_metric_comparison_chart(df, numeric_columns[:5])
            charts.append(chart3)
        
        return charts

    def _create_score_distribution_chart(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create score distribution chart"""
        plt.figure(figsize=(10, 6))
        plt.hist(df['score'], bins=20, alpha=0.7, color='#3B82F6', edgecolor='black')
        plt.title('Score Distribution')
        plt.xlabel('Score')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            'title': 'Score Distribution',
            'image': image_base64,
            'description': 'Distribution of scores across all records in the dataset.'
        }

    def _create_performance_trend_chart(self, df: pd.DataFrame, date_column: str) -> Dict[str, Any]:
        """Create performance trend chart"""
        plt.figure(figsize=(10, 6))
        
        # Convert date column to datetime
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.dropna(subset=[date_column])
        
        if len(df) > 0:
            # Sort by date and plot
            df_sorted = df.sort_values(date_column)
            plt.plot(df_sorted[date_column], df_sorted['score'], marker='o', linewidth=2, markersize=4)
            plt.title('Performance Trend Over Time')
            plt.xlabel('Date')
            plt.ylabel('Score')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            'title': 'Performance Trend Over Time',
            'image': image_base64,
            'description': 'Trend of scores over time showing performance progression.'
        }

    def _create_metric_comparison_chart(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Create metric comparison chart"""
        plt.figure(figsize=(10, 6))
        
        # Calculate means for each metric
        means = [df[col].mean() for col in columns if col in df.columns]
        labels = [col for col in columns if col in df.columns]
        
        if means:
            bars = plt.bar(labels, means, color=['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'][:len(means)])
            plt.title('Metric Comparison')
            plt.xlabel('Metrics')
            plt.ylabel('Average Value')
            plt.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            
            # Add value labels on bars
            for bar, mean in zip(bars, means):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{mean:.2f}', ha='center', va='bottom')
        
        # Save to buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            'title': 'Metric Comparison',
            'image': image_base64,
            'description': 'Comparison of average values across different metrics.'
        }

    def _generate_insights(self, data: List[Dict[str, Any]]) -> List[str]:
        """Generate insights from data"""
        insights = []
        
        if not data:
            return ["No data available for analysis"]
        
        # Calculate basic statistics
        scores = [item.get('score', 0) for item in data if item.get('score') is not None]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            insights.append(f"Average score across all records: {avg_score:.2f}")
            insights.append(f"Score range: {min_score:.2f} to {max_score:.2f}")
            
            if avg_score >= 80:
                insights.append("Overall performance is excellent with high scores across the board")
            elif avg_score >= 60:
                insights.append("Overall performance is good with room for improvement in certain areas")
            else:
                insights.append("Overall performance needs attention and optimization")
        
        # Analyze patterns
        if len(data) > 10:
            insights.append(f"Analysis based on {len(data)} records provides statistical significance")
        
        return insights

    def _generate_recommendations(self, data: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on data"""
        recommendations = []
        
        if not data:
            return ["No data available for recommendations"]
        
        scores = [item.get('score', 0) for item in data if item.get('score') is not None]
        
        if scores:
            avg_score = sum(scores) / len(scores)
            
            if avg_score < 60:
                recommendations.append("Implement immediate optimization strategies to improve performance")
                recommendations.append("Review and adjust targeting parameters")
                recommendations.append("Consider creative refresh to boost engagement")
            elif avg_score < 80:
                recommendations.append("Focus on incremental improvements in underperforming areas")
                recommendations.append("Test new audience segments to expand reach")
                recommendations.append("Optimize bid strategies for better cost efficiency")
            else:
                recommendations.append("Maintain current performance levels")
                recommendations.append("Explore opportunities for further optimization")
                recommendations.append("Consider scaling successful strategies")
        
        return recommendations

    def _get_field_descriptions(self, sample_row: Dict[str, Any]) -> Dict[str, str]:
        """Get field descriptions for data dictionary"""
        descriptions = {
            'score': 'Performance score (0-100)',
            'date': 'Date of measurement',
            'campaign_id': 'Unique campaign identifier',
            'report_id': 'Unique report identifier',
            'metric_name': 'Name of the measured metric',
            'value': 'Raw metric value',
            'weight': 'Weight assigned to this metric',
            'status': 'Processing status'
        }
        
        # Add descriptions for any fields not in the default list
        for field in sample_row.keys():
            if field not in descriptions:
                descriptions[field] = f'Field: {field}'
        
        return descriptions

# Create a singleton instance
pdf_generator = PDFGenerator() 