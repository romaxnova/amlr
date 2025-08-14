import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import markdown
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
import os
from datetime import datetime
from typing import List, Dict
import re

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
        """Export summary to PDF using ReportLab (primary method)"""
        if not filename:
            filename = f"aml_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        try:
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
                alignment=1,  # Center alignment
                textColor=colors.HexColor('#2c3e50')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=20,
                spaceAfter=12,
                textColor=colors.HexColor('#34495e')
            )
            
            subheading_style = ParagraphStyle(
                'CustomSubHeading',
                parent=styles['Heading3'],
                fontSize=12,
                spaceBefore=15,
                spaceAfter=10,
                textColor=colors.HexColor('#7f8c8d')
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=10,
                spaceBefore=6,
                spaceAfter=6,
                alignment=4  # Justify
            )
            
            # Build document
            story = []
            
            # Title
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Process summary text
            lines = summary_text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    story.append(Spacer(1, 12))
                    continue
                
                # Handle markdown formatting
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], title_style))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], heading_style))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], subheading_style))
                elif line.startswith('- ') or line.startswith('* '):
                    # Handle bullet points
                    formatted_line = self._format_markdown_text(f"• {line[2:]}")
                    story.append(Paragraph(formatted_line, body_style))
                elif line.startswith(('1. ', '2. ', '3. ', '4. ', '5. ', '6. ', '7. ', '8. ', '9. ')):
                    # Handle numbered lists
                    formatted_line = self._format_markdown_text(line)
                    story.append(Paragraph(formatted_line, body_style))
                else:
                    # Regular paragraph
                    formatted_line = self._format_markdown_text(line)
                    story.append(Paragraph(formatted_line, body_style))
            
            # Build PDF
            doc.build(story)
            return filepath
            
        except Exception as e:
            print(f"ReportLab PDF creation failed: {e}")
            
            # Fallback to WeasyPrint if available
            if WEASYPRINT_AVAILABLE:
                try:
                    return self._export_with_weasyprint(summary_text, title, filepath)
                except Exception as e2:
                    print(f"WeasyPrint also failed: {e2}")
            
            # Final fallback to text file
            text_filepath = filepath.replace('.pdf', '.txt')
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(f"{title}\n{'='*len(title)}\n\n{summary_text}")
            return text_filepath
    
    def _export_with_weasyprint(self, summary_text: str, title: str, filepath: str) -> str:
        """Export using WeasyPrint as fallback"""
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
        
        # Convert HTML to PDF
        HTML(string=html_doc).write_pdf(filepath)
        return filepath
    
    def _format_markdown_text(self, text):
        """Format markdown-style text for ReportLab"""
        # Handle bold text **text** or __text__
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
        
        # Handle italic text *text* or _text_
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)
        
        # Handle code `text`
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)
        
        # Escape XML characters that might break ReportLab
        text = text.replace('&', '&amp;')
        
        # Be more careful with < and > - only escape them if they're not our tags
        temp_text = text
        # Temporarily replace our tags
        temp_text = temp_text.replace('<b>', '___BOLD_START___')
        temp_text = temp_text.replace('</b>', '___BOLD_END___')
        temp_text = temp_text.replace('<i>', '___ITALIC_START___')
        temp_text = temp_text.replace('</i>', '___ITALIC_END___')
        temp_text = temp_text.replace('<font name="Courier">', '___CODE_START___')
        temp_text = temp_text.replace('</font>', '___CODE_END___')
        
        # Now escape remaining < and >
        temp_text = temp_text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore our tags
        temp_text = temp_text.replace('___BOLD_START___', '<b>')
        temp_text = temp_text.replace('___BOLD_END___', '</b>')
        temp_text = temp_text.replace('___ITALIC_START___', '<i>')
        temp_text = temp_text.replace('___ITALIC_END___', '</i>')
        temp_text = temp_text.replace('___CODE_START___', '<font name="Courier">')
        temp_text = temp_text.replace('___CODE_END___', '</font>')
        
        return temp_text
    
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
