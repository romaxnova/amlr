import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import os
from datetime import datetime
from typing import List, Dict

class ExportManager:
    def __init__(self, output_dir: str = "./exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_to_csv(self, papers: List[Dict], filename: str = None) -> str:
        """Export papers to CSV format"""
        if not filename:
            filename = f"aml_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert to DataFrame
        df = pd.DataFrame(papers)
        
        # Reorder columns for better readability
        column_order = ['title', 'authors', 'journal', 'publish_date', 'article_type', 
                       'pmid', 'main_findings', 'num_references', 'abstract']
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in df.columns]
        df = df[available_columns]
        
        # Export to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return filepath
    
    def export_summary_to_pdf(self, summary_text: str, title: str = "AML Research Summary", 
                             filename: str = None) -> str:
        """Export markdown summary to PDF using WeasyPrint"""
        if not filename:
            filename = f"aml_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert markdown to HTML
        html_content = markdown.markdown(summary_text, extensions=['tables', 'toc'])
        
        # Create complete HTML document
        html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: #333;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 3px solid #3498db;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #34495e;
                    margin-top: 30px;
                    border-left: 4px solid #3498db;
                    padding-left: 15px;
                }}
                h3 {{
                    color: #7f8c8d;
                    margin-top: 25px;
                }}
                p {{
                    text-align: justify;
                    margin-bottom: 15px;
                }}
                ul, ol {{
                    margin-bottom: 15px;
                }}
                li {{
                    margin-bottom: 5px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 1px solid #ecf0f1;
                }}
                .date {{
                    color: #7f8c8d;
                    font-size: 0.9em;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p class="date">Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}</p>
            </div>
            {html_content}
        </body>
        </html>
        """
        
        try:
            # Convert HTML to PDF
            HTML(string=html_doc).write_pdf(filepath)
            return filepath
        except Exception as e:
            print(f"Error creating PDF: {e}")
            # Fallback to simple text file
            text_filepath = filepath.replace('.pdf', '.txt')
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(summary_text)
            return text_filepath
    
    def export_summary_to_pdf_reportlab(self, summary_text: str, title: str = "AML Research Summary", 
                                       filename: str = None) -> str:
        """Alternative PDF export using ReportLab (fallback method)"""
        if not filename:
            filename = f"aml_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=12
        )
        
        # Build document
        story = []
        
        # Title
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Process summary text
        lines = summary_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 12))
            elif line.startswith('# '):
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith('## '):
                story.append(Paragraph(line[3:], heading_style))
            elif line.startswith('### '):
                story.append(Paragraph(line[4:], styles['Heading3']))
            else:
                story.append(Paragraph(line, styles['Normal']))
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def create_research_dashboard_data(self, papers: List[Dict]) -> Dict:
        """Create data structure for dashboard visualizations"""
        df = pd.DataFrame(papers)
        
        dashboard_data = {}
        
        # Papers by year
        if 'publish_date' in df.columns:
            df['year'] = pd.to_datetime(df['publish_date'], errors='coerce').dt.year
            papers_by_year = df.groupby('year').size().reset_index(name='count')
            dashboard_data['papers_by_year'] = papers_by_year.to_dict('records')
        
        # Papers by article type
        if 'article_type' in df.columns:
            type_counts = df['article_type'].value_counts().reset_index()
            type_counts.columns = ['type', 'count']
            dashboard_data['papers_by_type'] = type_counts.to_dict('records')
        
        # Top journals
        if 'journal' in df.columns:
            journal_counts = df['journal'].value_counts().head(10).reset_index()
            journal_counts.columns = ['journal', 'count']
            dashboard_data['top_journals'] = journal_counts.to_dict('records')
        
        # Recent papers (last 30 days)
        if 'publish_date' in df.columns:
            recent_date = pd.Timestamp.now() - pd.Timedelta(days=30)
            recent_papers = df[pd.to_datetime(df['publish_date'], errors='coerce') > recent_date]
            dashboard_data['recent_papers_count'] = len(recent_papers)
        
        return dashboard_data
