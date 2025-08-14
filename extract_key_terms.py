#!/usr/bin/env python3
"""
Extract key terms for existing papers in the database
"""
import sys
import os
sys.path.append('.')

from src.database import DatabaseManager
from src.ai_analyzer import AIAnalyzer
import json

def extract_key_terms_for_existing_papers():
    """Extract key terms for all papers that don't have them yet"""
    db = DatabaseManager()
    analyzer = AIAnalyzer()
    
    if not analyzer.client:
        print("Error: AI client not available. Check your XAI_API_KEY.")
        return
    
    # Get papers without key terms
    papers = db.get_all_papers()
    papers_to_process = []
    
    print(f"Checking {len(papers)} papers for key terms...")
    
    for paper in papers:
        key_terms_json = paper.get('key_terms')
        if key_terms_json is None:
            key_terms = []
        else:
            try:
                key_terms = json.loads(key_terms_json)
            except (json.JSONDecodeError, TypeError):
                key_terms = []
        
        if not key_terms:  # No key terms extracted yet
            papers_to_process.append(paper)
    
    print(f"Found {len(papers_to_process)} papers without key terms.")
    
    if not papers_to_process:
        print("All papers already have key terms extracted!")
        return
    
    # Process papers in batches to avoid overwhelming the API
    processed = 0
    total = len(papers_to_process)
    
    for i, paper in enumerate(papers_to_process):
        try:
            print(f"\nProcessing paper {i+1}/{total}: PMID {paper.get('pmid')}")
            print(f"Title: {paper.get('title', '')[:60]}...")
            
            # Extract key terms
            key_terms = analyzer.extract_key_terms(dict(paper))
            
            if key_terms:
                print(f"Extracted {len(key_terms)} key terms: {key_terms[:5]}...")
                
                # Update the paper with key terms
                paper_dict = dict(paper)
                paper_dict['key_terms'] = key_terms
                
                # Update in database
                if db.insert_paper(paper_dict):
                    processed += 1
                    print("✓ Updated paper with key terms")
                else:
                    print("✗ Failed to update paper")
            else:
                print("No key terms extracted")
                
        except Exception as e:
            print(f"Error processing paper {paper.get('pmid')}: {e}")
            continue
        
        # Add a small delay to be respectful to the API
        if i % 5 == 0 and i > 0:
            print(f"\nProcessed {i} papers so far...")
            import time
            time.sleep(1)
    
    print(f"\n✓ Extraction complete! Updated {processed}/{total} papers with key terms.")
    
    # Check the results
    import sqlite3
    conn = sqlite3.connect('./data/research.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM key_terms')
    key_terms_count = cursor.fetchone()[0]
    print(f"Total unique key terms in database: {key_terms_count}")
    
    if key_terms_count > 0:
        cursor.execute('SELECT term, frequency FROM key_terms ORDER BY frequency DESC LIMIT 10')
        top_terms = cursor.fetchall()
        print("\nTop 10 key terms:")
        for term, freq in top_terms:
            print(f"  {term}: {freq}")
    
    conn.close()

if __name__ == "__main__":
    extract_key_terms_for_existing_papers()
