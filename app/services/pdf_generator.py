from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from app.models.report import PDFReportData
from typing import Optional
import logging
import tempfile
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Service for generating executive PDF reports."""
    
    def __init__(self):
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
        # Create templates directory if it doesn't exist
        os.makedirs(template_dir, exist_ok=True)
        
        # Create default template if it doesn't exist
        self._ensure_template_exists(template_dir)
    
    def _ensure_template_exists(self, template_dir: str):
        """Ensure the PDF template exists."""
        template_path = os.path.join(template_dir, "executive_report.html")
        
        if not os.path.exists(template_path):
            logger.info("Creating default PDF template")
            template_content = self._get_default_template()
            with open(template_path, 'w') as f:
                f.write(template_content)
    
    def _get_default_template(self) -> str:
        """Get the default HTML template for PDF generation."""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>RetentionOps Executive Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .header .subtitle {
            margin-top: 10px;
            opacity: 0.9;
        }
        .section {
            margin-bottom: 30px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .section h2 {
            margin-top: 0;
            color: #667eea;
            font-size: 20px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        .metric {
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }
        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .table th {
            background: #667eea;
            color: white;
        }
        .table tr:hover {
            background: #f5f5f5;
        }
        .red-flag {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .red-flag.critical {
            background: #fee;
            border-color: #c00;
        }
        .red-flag.high {
            background: #ffd;
            border-color: #f90;
        }
        .red-flag.medium {
            background: #fff3cd;
            border-color: #fc0;
        }
        .flag-severity {
            font-weight: bold;
            text-transform: uppercase;
            font-size: 11px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .neutral { color: #6c757d; }
    </style>
</head>
<body>
    <div class="header">
        <h1>RetentionOps Executive Report</h1>
        <div class="subtitle">
            <strong>Brand:</strong> {{ brand_name }} | 
            <strong>Date:</strong> {{ report_date.strftime('%B %d, %Y') }}
        </div>
    </div>

    {% if canvas_summary %}
    <div class="section">
        <h2>Retention Canvas Summary</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Total Mechanics</div>
                <div class="metric-value">{{ canvas_summary.total_mechanics }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Active Mechanics</div>
                <div class="metric-value">{{ canvas_summary.active_mechanics }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Coverage</div>
                <div class="metric-value">{{ "%.1f"|format(canvas_summary.coverage_percentage) }}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Avg Maturity</div>
                <div class="metric-value">{{ "%.1f"|format(canvas_summary.average_maturity) }}/3</div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if gap_analysis %}
    <div class="section">
        <h2>Competitor Gap Analysis</h2>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-label">Competitors Analyzed</div>
                <div class="metric-value">{{ gap_analysis.total_competitors }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Lagging</div>
                <div class="metric-value negative">{{ gap_analysis.lagging_mechanics }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">At Parity</div>
                <div class="metric-value neutral">{{ gap_analysis.parity_mechanics }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Leading</div>
                <div class="metric-value positive">{{ gap_analysis.leading_mechanics }}</div>
            </div>
        </div>
        <p style="margin-top: 15px;"><strong>Overall Position:</strong> {{ gap_analysis.overall_position }}</p>
    </div>
    {% endif %}

    {% if roi_analysis %}
    <div class="section">
        <h2>ROI Break-Even Analysis</h2>
        <table class="table">
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Break-Even GGR Growth</td>
                <td>{{ "%.2f"|format(roi_analysis.break_even_ggr_growth) }}%</td>
            </tr>
            <tr>
                <td>Break-Even Bonus Reduction</td>
                <td>{{ "%.2f"|format(roi_analysis.break_even_bonus_reduction) }}%</td>
            </tr>
            <tr>
                <td>Recommended Investment</td>
                <td>${{ "{:,.0f}"|format(roi_analysis.recommended_investment) }}</td>
            </tr>
            <tr>
                <td>Expected ROI</td>
                <td class="positive">{{ "%.1f"|format(roi_analysis.expected_roi) }}%</td>
            </tr>
        </table>
    </div>
    {% endif %}

    {% if top_red_flags %}
    <div class="section">
        <h2>Top Critical Red Flags</h2>
        {% for flag in top_red_flags %}
        <div class="red-flag {{ flag.severity.lower() }}">
            <div class="flag-severity">{{ flag.severity }}</div>
            <div><strong>{{ flag.description }}</strong></div>
            {% if flag.mechanic %}
            <div style="font-size: 12px; color: #666; margin-top: 5px;">
                Mechanic: {{ flag.mechanic }}
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="footer">
        <p>Generated by RetentionOps API | {{ report_date.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        <p>This report is confidential and intended for internal use only.</p>
    </div>
</body>
</html>"""
    
    def generate_executive_report(
        self,
        report_data: PDFReportData
    ) -> bytes:
        """
        Generate an executive PDF report.
        
        Args:
            report_data: Data for the report
            
        Returns:
            bytes: PDF file content
        """
        try:
            # Load template
            template = self.env.get_template("executive_report.html")
            
            # Render HTML
            html_content = template.render(
                brand_name=report_data.brand_name,
                report_date=report_data.report_date,
                canvas_summary=report_data.canvas_summary,
                gap_analysis=report_data.gap_analysis,
                roi_analysis=report_data.roi_analysis,
                top_red_flags=report_data.top_red_flags
            )
            
            # Generate PDF
            logger.info(f"Generating PDF report for {report_data.brand_name}")
            
            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_path = tmp_file.name
            
            # Generate PDF using WeasyPrint
            HTML(string=html_content).write_pdf(pdf_path)
            
            # Read PDF content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Clean up temporary file
            os.unlink(pdf_path)
            
            logger.info(f"PDF report generated successfully: {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def generate_simple_report(
        self,
        brand_name: str,
        title: str,
        content: str
    ) -> bytes:
        """
        Generate a simple PDF report with custom content.
        
        Args:
            brand_name: Brand name
            title: Report title
            content: Report content (HTML)
            
        Returns:
            bytes: PDF file content
        """
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
                    .header {{ background: #667eea; color: white; padding: 20px; border-radius: 10px; margin-bottom: 30px; }}
                    .header h1 {{ margin: 0; }}
                    .content {{ line-height: 1.6; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p>Brand: {brand_name} | Date: {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                <div class="content">
                    {content}
                </div>
            </body>
            </html>
            """
            
            # Create temporary file for PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_path = tmp_file.name
            
            # Generate PDF
            HTML(string=html_content).write_pdf(pdf_path)
            
            # Read PDF content
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Clean up temporary file
            os.unlink(pdf_path)
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating simple PDF report: {e}")
            raise


# Singleton instance
pdf_generator = PDFGenerator()
