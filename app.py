from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
from dotenv import load_dotenv
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import our modules
from src.database import DatabaseManager
from src.pubmed_scraper import PubMedScraper
from src.ai_analyzer import AIAnalyzer
from src.export_manager import ExportManager

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize components
db = DatabaseManager()
scraper = PubMedScraper()
analyzer = AIAnalyzer()
exporter = ExportManager()

@app.route('/')
def index():
    """Main dashboard"""
    stats = db.get_stats()
    return render_template('index.html', stats=stats, current_endpoint='index')

@app.route('/update_research', methods=['POST'])
def update_research():
    """Update research database"""
    try:
        # Get current date and last update date
        current_date = datetime.now().strftime('%Y-%m-%d')
        last_update = db.get_last_update_date()
        
        # Check if this is initial run or update
        is_initial = request.form.get('initial', 'false').lower() == 'true'
        
        if is_initial:
            # Initial run - get all papers from the last year
            print("Starting initial research database population...")
            total_papers = scraper.get_paper_count()
            flash(f"Found {total_papers} papers to process. This may take a while...", "info")
        else:
            # Update run - get papers since last update
            print(f"Updating database with papers since {last_update}...")
            total_papers = scraper.get_paper_count(after_date=last_update)
            
            if total_papers == 0:
                flash("No new papers found since last update.", "info")
                return redirect(url_for('index'))
        
        # Scrape papers
        papers = scraper.scrape_multiple_pages(
            total_results=min(total_papers, 243),  # Limit to known total
            page_size=50,
            after_date=None if is_initial else last_update
        )
        
        # Process papers with AI analysis
        processed_count = 0
        for paper in papers:
            try:
                # Analyze paper with AI
                main_findings = analyzer.analyze_paper(paper)
                paper['main_findings'] = main_findings
                
                # Insert into database
                if db.insert_paper(paper):
                    processed_count += 1
                
            except Exception as e:
                print(f"Error processing paper {paper.get('pmid', 'unknown')}: {e}")
                continue
        
        # Update last update date
        db.update_last_update_date(current_date)
        
        flash(f"Successfully processed {processed_count} papers!", "success")
        
    except Exception as e:
        flash(f"Error updating research database: {str(e)}", "error")
    
    return redirect(url_for('index'))

@app.route('/generate_summary')
def generate_summary():
    """Show summary generation page"""
    return render_template('summary.html', current_endpoint='generate_summary')

@app.route('/api/generate_summary', methods=['POST'])
def api_generate_summary():
    """Generate comprehensive summary"""
    try:
        language = request.json.get('language', 'en')
        
        # Get all papers from database
        papers = db.get_all_papers()
        
        if not papers:
            return jsonify({'error': 'No papers found in database'}), 400
        
        # Generate summary
        summary = analyzer.generate_comprehensive_summary(papers, language)
        
        return jsonify({
            'summary': summary,
            'total_papers': len(papers),
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export_summary', methods=['POST'])
def api_export_summary():
    """Export summary to PDF"""
    try:
        summary_text = request.json.get('summary', '')
        language = request.json.get('language', 'en')
        
        if not summary_text:
            return jsonify({'error': 'No summary provided'}), 400
        
        # Export to PDF
        filename = exporter.export_summary_to_pdf(
            summary_text, 
            title=f"AML Research Summary ({language.upper()})"
        )
        
        return send_file(filename, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/browse')
def browse():
    """Browse research database"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filters
    search_query = request.args.get('search', '')
    article_type = request.args.get('type', '')
    year = request.args.get('year', '')
    
    # Get papers (for now, get all - in production, implement pagination)
    papers = db.get_all_papers()
    
    # Apply filters
    if search_query:
        papers = [p for p in papers if search_query.lower() in p.get('title', '').lower() 
                 or search_query.lower() in p.get('abstract', '').lower()]
    
    if article_type:
        papers = [p for p in papers if p.get('article_type') == article_type]
    
    if year:
        papers = [p for p in papers if p.get('publish_date', '').startswith(year)]
    
    # Get unique values for filters
    all_papers = db.get_all_papers()
    article_types = list(set(p.get('article_type', '') for p in all_papers if p.get('article_type')))
    years = list(set(p.get('publish_date', '')[:4] for p in all_papers if p.get('publish_date')))
    years.sort(reverse=True)
    
    return render_template('browse.html', 
                         papers=papers, 
                         article_types=article_types,
                         years=years,
                         search_query=search_query,
                         selected_type=article_type,
                         selected_year=year,
                         current_endpoint='browse')

@app.route('/api/export_csv')
def api_export_csv():
    """Export database to CSV"""
    try:
        papers = db.get_all_papers()
        filename = exporter.export_to_csv(papers)
        return send_file(filename, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()
        papers = db.get_all_papers()
        dashboard_data = exporter.create_research_dashboard_data(papers)
        
        return jsonify({
            'stats': stats,
            'dashboard_data': dashboard_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html', current_endpoint='analytics')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
