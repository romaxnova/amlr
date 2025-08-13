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
                
                # Extract key terms
                key_terms = analyzer.extract_key_terms(paper)
                paper['key_terms'] = key_terms
                
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
    # Get existing summary info
    summary_info = {}
    for lang in ['en', 'fr', 'ru']:
        existing = db.get_latest_summary(lang)
        summary_info[lang] = {
            'exists': existing is not None,
            'version': existing['version'] if existing else 0,
            'paper_count': existing['paper_count'] if existing else 0,
            'last_update': existing['created_at'] if existing else None
        }
    
    # Get key terms for filtering
    key_terms = db.get_all_key_terms()
    
    return render_template('summary.html', 
                         current_endpoint='generate_summary',
                         summary_info=summary_info,
                         key_terms=key_terms)

@app.route('/api/generate_summary', methods=['POST'])
def api_generate_summary():
    """Generate or update comprehensive summary"""
    try:
        language = request.json.get('language', 'en')
        force_regenerate = request.json.get('force_regenerate', False)
        selected_terms = request.json.get('selected_terms', [])
        
        # Get papers (filtered by terms if specified)
        if selected_terms:
            papers = db.get_papers_by_terms(selected_terms)
        else:
            papers = db.get_all_papers()
        
        if not papers:
            return jsonify({'error': 'No papers found'}), 400
        
        # Check if we have an existing summary
        existing_summary = db.get_latest_summary(language)
        
        if existing_summary and not force_regenerate:
            # Check if there are new papers since last summary
            latest_paper_date = existing_summary['latest_paper_date']
            new_papers = db.get_papers_after_date(latest_paper_date)
            
            if not new_papers:
                # No new papers - return existing summary with info message
                return jsonify({
                    'summary': existing_summary['content'],
                    'total_papers': existing_summary['paper_count'],
                    'new_papers': 0,
                    'version': existing_summary['version'],
                    'update_type': 'no_update',
                    'message': 'No new papers found since last update. Displaying existing summary.',
                    'trends': {
                        'key_trends': existing_summary['key_trends'],
                        'therapeutic_targets': existing_summary['therapeutic_targets'],
                        'prognostic_markers': existing_summary['prognostic_markers']
                    },
                    'generated_at': existing_summary['created_at']
                })
            else:
                # Generate incremental update
                updated_content = analyzer.generate_incremental_summary(
                    existing_summary['content'], new_papers, language
                )
                
                # Extract trends from all papers
                trends = analyzer.extract_research_trends(papers)
                
                # Save updated summary
                version = db.save_research_summary(
                    updated_content, language, len(papers),
                    max(p['publish_date'] for p in papers if p.get('publish_date')),
                    trends
                )
                
                return jsonify({
                    'summary': updated_content,
                    'total_papers': len(papers),
                    'new_papers': len(new_papers),
                    'version': version,
                    'update_type': 'incremental',
                    'message': f'Summary updated with {len(new_papers)} new papers.',
                    'trends': trends,
                    'generated_at': datetime.now().isoformat()
                })
        else:
            # Generate new complete summary
            summary = analyzer.generate_comprehensive_summary(papers, language)
            trends = analyzer.extract_research_trends(papers)
            
            # Save new summary
            version = db.save_research_summary(
                summary, language, len(papers),
                max(p['publish_date'] for p in papers if p.get('publish_date')),
                trends
            )
            
            return jsonify({
                'summary': summary,
                'total_papers': len(papers),
                'new_papers': len(papers),
                'version': version,
                'update_type': 'complete',
                'message': 'New comprehensive summary generated.',
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            })
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        import traceback
        traceback.print_exc()
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

@app.route('/api/key_terms')
def api_key_terms():
    """Get all key terms with frequencies"""
    try:
        terms = db.get_all_key_terms()
        return jsonify({'key_terms': terms})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_summary/<language>')
def api_get_summary(language):
    """Get existing summary for a language"""
    try:
        summary = db.get_latest_summary(language)
        if summary:
            return jsonify({
                'summary': summary['content'],
                'total_papers': summary['paper_count'],
                'version': summary['version'],
                'update_type': 'existing',
                'trends': {
                    'key_trends': summary['key_trends'],
                    'therapeutic_targets': summary['therapeutic_targets'],
                    'prognostic_markers': summary['prognostic_markers']
                },
                'generated_at': summary['created_at'],
                'exists': True
            })
        else:
            return jsonify({'exists': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html', current_endpoint='analytics')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
