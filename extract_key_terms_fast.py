#!/usr/bin/env python3
"""
Fast key terms extraction from existing abstracts using local text processing
"""
import sys
import os
sys.path.append('.')

from src.database import DatabaseManager
import sqlite3
import re
import json
from collections import Counter

def extract_key_terms_fast():
    """Extract key terms from abstracts using local text processing"""
    print("Starting fast key terms extraction from abstracts...")
    
    # Connect directly to database for efficiency
    conn = sqlite3.connect('./data/research.db')
    cursor = conn.cursor()
    
    # Get all papers with abstracts
    cursor.execute('SELECT id, pmid, title, abstract FROM papers WHERE abstract IS NOT NULL')
    papers = cursor.fetchall()
    
    print(f"Processing {len(papers)} papers with abstracts...")
    
    # Define patterns for medical/research terms relevant to AML/TP53
    medical_patterns = [
        # Genes and proteins
        r'\b(TP53|p53|MDM2|ASXL1|DNMT3A|TET2|IDH1|IDH2|NPM1|FLT3|CEBPA|RUNX1|KIT|NRAS|KRAS)\b',
        r'\b(BCL2|MCL1|BAX|BAK|PUMA|NOXA|p21|p16|RB1|E2F1)\b',
        
        # Drugs and treatments
        r'\b(venetoclax|azacitidine|decitabine|cytarabine|daunorubicin|idarubicin|mitoxantrone)\b',
        r'\b(tetrandrine|CPX-351|gemtuzumab|midostaurin|gilteritinib|quizartinib)\b',
        r'\b(allogeneic|autologous|transplantation|HSCT|chemotherapy|hypomethylating)\b',
        
        # Clinical terms
        r'\b(overall survival|progression-free survival|relapse-free survival|event-free survival)\b',
        r'\b(complete remission|partial remission|refractory|relapsed|minimal residual disease)\b',
        r'\b(cytogenetics|karyotype|complex karyotype|monosomal karyotype)\b',
        r'\b(blast count|bone marrow|peripheral blood|flow cytometry)\b',
        
        # Molecular mechanisms
        r'\b(apoptosis|cell cycle|DNA damage|DNA repair|oxidative stress)\b',
        r'\b(methylation|demethylation|epigenetic|chromatin|transcription)\b',
        r'\b(signaling pathway|tumor suppressor|oncogene|mutation|wild-type)\b',
        
        # Research techniques
        r'\b(qPCR|RT-PCR|western blot|immunofluorescence|CRISPR|RNA-seq|ChIP-seq)\b',
        r'\b(cell culture|xenograft|mouse model|in vitro|in vivo)\b',
        
        # Clinical classifications
        r'\b(ELN risk|WHO classification|FAB classification|cytogenetic risk)\b',
        r'\b(therapy-related|secondary AML|de novo|myelodysplastic syndrome)\b'
    ]
    
    # Compile patterns for efficiency
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in medical_patterns]
    
    # Track terms across all papers
    all_terms = Counter()
    paper_terms_data = []
    
    for paper_id, pmid, title, abstract in papers:
        # Extract terms from title and abstract
        text = f"{title} {abstract}".lower()
        paper_terms = set()
        
        # Find matches for each pattern
        for pattern in compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Clean and normalize the term
                clean_term = match.strip().upper()
                if len(clean_term) >= 2:  # Minimum term length
                    paper_terms.add(clean_term)
        
        # Filter out overly general terms
        excluded_terms = {
            'ACUTE MYELOID LEUKEMIA', 'AML', 'LEUKEMIA', 'CANCER', 'TUMOR', 
            'CELL', 'CELLS', 'PATIENT', 'PATIENTS', 'TREATMENT', 'THERAPY'
        }
        
        paper_terms = paper_terms - excluded_terms
        
        # Limit to top terms (by frequency in abstract)
        if len(paper_terms) > 8:
            # Count frequency of each term in the abstract
            term_counts = {}
            for term in paper_terms:
                term_counts[term] = len(re.findall(re.escape(term), text, re.IGNORECASE))
            
            # Keep top 8 most frequent terms
            paper_terms = set(sorted(term_counts.keys(), key=lambda x: term_counts[x], reverse=True)[:8])
        
        if paper_terms:
            print(f"PMID {pmid}: {len(paper_terms)} terms - {list(paper_terms)[:3]}...")
            
            # Update paper with key terms
            terms_json = json.dumps(list(paper_terms))
            cursor.execute('UPDATE papers SET key_terms = ? WHERE id = ?', (terms_json, paper_id))
            
            # Track for global statistics
            all_terms.update(paper_terms)
            
            # Prepare paper_terms data
            for term in paper_terms:
                paper_terms_data.append((paper_id, term))
    
    print(f"\nUpdated {len([p for p in papers if paper_terms])} papers with key terms")
    
    # Insert unique terms into key_terms table
    print("Inserting unique terms into key_terms table...")
    cursor.execute('DELETE FROM key_terms')  # Clear existing
    
    term_to_id = {}  # Map term names to their IDs
    for term, frequency in all_terms.items():
        cursor.execute('INSERT INTO key_terms (term, frequency) VALUES (?, ?)', (term, frequency))
        term_id = cursor.lastrowid
        term_to_id[term] = term_id
    
    # Insert paper-term relationships using term_id
    print("Inserting paper-term relationships...")
    cursor.execute('DELETE FROM paper_terms')  # Clear existing
    
    for paper_id, term in paper_terms_data:
        term_id = term_to_id.get(term)
        if term_id:
            cursor.execute('INSERT INTO paper_terms (paper_id, term_id) VALUES (?, ?)', (paper_id, term_id))
    
    conn.commit()
    
    # Report results
    cursor.execute('SELECT COUNT(*) FROM key_terms')
    terms_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM paper_terms')
    relationships_count = cursor.fetchone()[0]
    
    print(f"\n✅ Extraction complete!")
    print(f"📊 Statistics:")
    print(f"   - Unique key terms: {terms_count}")
    print(f"   - Paper-term relationships: {relationships_count}")
    
    # Show top terms
    cursor.execute('SELECT term, frequency FROM key_terms ORDER BY frequency DESC LIMIT 15')
    top_terms = cursor.fetchall()
    
    print(f"\n🔝 Top 15 key terms:")
    for i, (term, freq) in enumerate(top_terms, 1):
        print(f"   {i:2d}. {term:<20} ({freq} papers)")
    
    conn.close()

if __name__ == "__main__":
    extract_key_terms_fast()
