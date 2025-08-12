#!/usr/bin/env python3
"""
AML Research Tool - Main Entry Point

A comprehensive tool for researching AML (Acute Myeloid Leukemia) and TP53 mutations
from PubMed literature using AI analysis.

Usage:
    python run.py                    # Start web server
    python run.py --update           # Update database only
    python run.py --init             # Initialize database with all papers
    python run.py --summary [lang]   # Generate summary (en/fr/ru)
"""

import argparse
import sys
import os
from dotenv import load_dotenv
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import DatabaseManager
from pubmed_scraper import PubMedScraper
from ai_analyzer import AIAnalyzer
from export_manager import ExportManager

def main():
    parser = argparse.ArgumentParser(description='AML Research Tool')
    parser.add_argument('--update', action='store_true', help='Update database with new papers')
    parser.add_argument('--init', action='store_true', help='Initialize database with all papers')
    parser.add_argument('--summary', choices=['en', 'fr', 'ru'], help='Generate summary in specified language')
    parser.add_argument('--port', type=int, default=5000, help='Port for web server')
    parser.add_argument('--host', default='localhost', help='Host for web server')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for required API key
    if not os.getenv('XAI_API_KEY'):
        print("Error: XAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your XAI API key.")
        return 1
    
    # Initialize components
    db = DatabaseManager()
    scraper = PubMedScraper()
    analyzer = AIAnalyzer()
    exporter = ExportManager()
    
    try:
        if args.init:
            print("Initializing database with all papers from the past year...")
            initialize_database(scraper, analyzer, db)
            
        elif args.update:
            print("Updating database with new papers...")
            update_database(scraper, analyzer, db)
            
        elif args.summary:
            print(f"Generating summary in {args.summary}...")
            generate_summary(analyzer, db, args.summary, exporter)
            
        else:
            # Start web server
            print(f"Starting AML Research Tool web server on {args.host}:{args.port}")
            print(f"Open your browser to: http://{args.host}:{args.port}")
            
            # Import and run Flask app
            from app import app
            app.run(host=args.host, port=args.port, debug=False)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def initialize_database(scraper, analyzer, db):
    """Initialize database with all papers from the past year"""
    print("Getting paper count...")
    total_papers = scraper.get_paper_count()
    print(f"Found {total_papers} papers to process")
    
    # Limit to known total for initial implementation
    papers_to_process = min(total_papers, 243)
    
    print(f"Scraping {papers_to_process} papers...")
    papers = scraper.scrape_multiple_pages(papers_to_process, page_size=50)
    
    processed_count = 0
    print("Analyzing papers with AI...")
    
    for i, paper in enumerate(papers, 1):
        try:
            print(f"Processing paper {i}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")
            
            # Analyze with AI
            main_findings = analyzer.analyze_paper(paper)
            paper['main_findings'] = main_findings
            
            # Insert into database
            if db.insert_paper(paper):
                processed_count += 1
                
        except Exception as e:
            print(f"Error processing paper {i}: {e}")
            continue
    
    # Update last update date
    db.update_last_update_date(datetime.now().strftime('%Y-%m-%d'))
    
    print(f"Successfully processed {processed_count} papers!")

def update_database(scraper, analyzer, db):
    """Update database with new papers since last update"""
    last_update = db.get_last_update_date()
    print(f"Last update was: {last_update}")
    
    # Get new papers
    new_papers = scraper.get_paper_count(after_date=last_update)
    
    if new_papers == 0:
        print("No new papers found since last update.")
        return
    
    print(f"Found {new_papers} new papers to process")
    
    papers = scraper.scrape_multiple_pages(new_papers, page_size=50, after_date=last_update)
    
    processed_count = 0
    print("Analyzing new papers with AI...")
    
    for i, paper in enumerate(papers, 1):
        try:
            print(f"Processing paper {i}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")
            
            # Analyze with AI
            main_findings = analyzer.analyze_paper(paper)
            paper['main_findings'] = main_findings
            
            # Insert into database
            if db.insert_paper(paper):
                processed_count += 1
                
        except Exception as e:
            print(f"Error processing paper {i}: {e}")
            continue
    
    # Update last update date
    db.update_last_update_date(datetime.now().strftime('%Y-%m-%d'))
    
    print(f"Successfully processed {processed_count} new papers!")

def generate_summary(analyzer, db, language, exporter):
    """Generate a comprehensive summary"""
    papers = db.get_all_papers()
    
    if not papers:
        print("No papers found in database. Please run --init first.")
        return
    
    print(f"Generating summary for {len(papers)} papers in {language}...")
    
    summary = analyzer.generate_comprehensive_summary(papers, language)
    
    # Save to file
    filename = f"aml_summary_{language}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save as markdown
    md_file = f"./exports/{filename}.md"
    os.makedirs("./exports", exist_ok=True)
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    
    # Save as PDF
    pdf_file = exporter.export_summary_to_pdf(summary, f"AML Research Summary ({language.upper()})", f"{filename}.pdf")
    
    print(f"Summary saved as:")
    print(f"  Markdown: {md_file}")
    print(f"  PDF: {pdf_file}")

if __name__ == "__main__":
    sys.exit(main())
