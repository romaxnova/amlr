import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "./data/research.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create papers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pmid TEXT UNIQUE,
                    title TEXT NOT NULL,
                    publish_date DATE,
                    article_type TEXT,
                    num_references INTEGER,
                    main_findings TEXT,
                    abstract TEXT,
                    authors TEXT,
                    journal TEXT,
                    key_terms TEXT,  -- JSON string of extracted key terms
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create research summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS research_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL,
                    language TEXT NOT NULL,
                    content TEXT NOT NULL,
                    paper_count INTEGER NOT NULL,
                    latest_paper_date DATE,
                    key_trends TEXT,  -- JSON string
                    therapeutic_targets TEXT,  -- JSON string
                    prognostic_markers TEXT,  -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(version, language)
                )
            ''')
            
            # Create key terms table for better filtering
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_terms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    category TEXT,  -- e.g., 'drug', 'gene', 'pathway', 'technique'
                    last_seen DATE
                )
            ''')
            
            # Create paper_terms junction table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paper_terms (
                    paper_id INTEGER,
                    term_id INTEGER,
                    relevance_score REAL DEFAULT 1.0,
                    PRIMARY KEY (paper_id, term_id),
                    FOREIGN KEY (paper_id) REFERENCES papers (id),
                    FOREIGN KEY (term_id) REFERENCES key_terms (id)
                )
            ''')
            
            # Create settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Initialize settings if not exists
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) 
                VALUES ('last_update_date', '2024-08-12')
            ''')
            
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) 
                VALUES ('summary_version', '0')
            ''')
            
            # Add key_terms column to existing papers table if it doesn't exist
            try:
                cursor.execute('ALTER TABLE papers ADD COLUMN key_terms TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.commit()
    
    def insert_paper(self, paper_data: Dict) -> bool:
        """Insert or update a paper in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert or update paper
                cursor.execute('''
                    INSERT OR REPLACE INTO papers 
                    (pmid, title, publish_date, article_type, num_references, 
                     main_findings, abstract, authors, journal, key_terms, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    paper_data.get('pmid'),
                    paper_data.get('title'),
                    paper_data.get('publish_date'),
                    paper_data.get('article_type'),
                    paper_data.get('num_references'),
                    paper_data.get('main_findings'),
                    paper_data.get('abstract'),
                    paper_data.get('authors'),
                    paper_data.get('journal'),
                    json.dumps(paper_data.get('key_terms', []))
                ))
                
                # Get the paper ID
                cursor.execute('SELECT id FROM papers WHERE pmid = ?', (paper_data.get('pmid'),))
                paper_id = cursor.fetchone()[0]
                
                # Insert key terms if they exist
                if paper_data.get('key_terms'):
                    self.insert_key_terms(paper_id, paper_data['key_terms'])
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error inserting paper: {e}")
            return False
            print(f"Error inserting paper: {e}")
            return False
    
    def get_all_papers(self, limit: Optional[int] = None) -> List[Dict]:
        """Retrieve all papers from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM papers ORDER BY publish_date DESC"
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_papers_after_date(self, date: str) -> List[Dict]:
        """Get papers published after a specific date"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM papers WHERE publish_date > ? ORDER BY publish_date DESC",
                (date,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def update_last_update_date(self, date: str):
        """Update the last update date in settings"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = 'last_update_date'",
                (date,)
            )
            conn.commit()
    
    def get_last_update_date(self) -> str:
        """Get the last update date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'last_update_date'")
            result = cursor.fetchone()
            return result[0] if result else "2024-08-12"
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total papers
            cursor.execute("SELECT COUNT(*) FROM papers")
            total_papers = cursor.fetchone()[0]
            
            # Papers by year
            cursor.execute('''
                SELECT strftime('%Y', publish_date) as year, COUNT(*) as count 
                FROM papers 
                WHERE publish_date IS NOT NULL 
                GROUP BY year 
                ORDER BY year DESC
            ''')
            papers_by_year = [{"year": row[0], "count": row[1]} for row in cursor.fetchall()]
            
            # Latest papers
            cursor.execute("SELECT MAX(publish_date) FROM papers")
            latest_date = cursor.fetchone()[0]
            
            return {
                "total_papers": total_papers,
                "papers_by_year": papers_by_year,
                "latest_date": latest_date,
                "last_update": self.get_last_update_date()
            }
    
    # New methods for smart summary and key terms
    
    def insert_key_terms(self, paper_id: int, terms: List[str]):
        """Insert key terms for a paper"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for term in terms:
                # Insert or update key term
                cursor.execute('''
                    INSERT OR REPLACE INTO key_terms (term, frequency, last_seen)
                    VALUES (?, 
                        COALESCE((SELECT frequency FROM key_terms WHERE term = ?), 0) + 1,
                        DATE('now'))
                ''', (term.lower(), term.lower()))
                
                # Get term ID
                cursor.execute('SELECT id FROM key_terms WHERE term = ?', (term.lower(),))
                term_id = cursor.fetchone()[0]
                
                # Link paper to term
                cursor.execute('''
                    INSERT OR REPLACE INTO paper_terms (paper_id, term_id, relevance_score)
                    VALUES (?, ?, 1.0)
                ''', (paper_id, term_id))
            
            conn.commit()
    
    def get_all_key_terms(self) -> List[Dict]:
        """Get all key terms with their frequencies"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT term, frequency, category, last_seen
                FROM key_terms 
                ORDER BY frequency DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_papers_by_terms(self, terms: List[str]) -> List[Dict]:
        """Get papers that contain specific key terms"""
        if not terms:
            return self.get_all_papers()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create placeholders for terms (case sensitive match)
            placeholders = ','.join(['?' for _ in terms])
            
            cursor.execute(f'''
                SELECT DISTINCT p.* FROM papers p
                JOIN paper_terms pt ON p.id = pt.paper_id
                JOIN key_terms kt ON pt.term_id = kt.id
                WHERE kt.term IN ({placeholders})
                ORDER BY p.publish_date DESC
            ''', terms)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def save_research_summary(self, content: str, language: str, paper_count: int, 
                             latest_paper_date: str, trends: Dict):
        """Save a generated research summary"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current version
            cursor.execute("SELECT value FROM settings WHERE key = 'summary_version'")
            current_version = int(cursor.fetchone()[0]) + 1
            
            # Insert new summary
            cursor.execute('''
                INSERT OR REPLACE INTO research_summaries 
                (version, language, content, paper_count, latest_paper_date, 
                 key_trends, therapeutic_targets, prognostic_markers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_version, language, content, paper_count, latest_paper_date,
                json.dumps(trends.get('key_trends', [])),
                json.dumps(trends.get('therapeutic_targets', [])),
                json.dumps(trends.get('prognostic_markers', []))
            ))
            
            # Update version in settings
            cursor.execute('''
                UPDATE settings SET value = ? WHERE key = 'summary_version'
            ''', (str(current_version),))
            
            conn.commit()
            return current_version
    
    def get_latest_summary(self, language: str = 'en') -> Optional[Dict]:
        """Get the latest research summary for a language"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM research_summaries 
                WHERE language = ? 
                ORDER BY version DESC 
                LIMIT 1
            ''', (language,))
            
            result = cursor.fetchone()
            if result:
                summary = dict(result)
                # Parse JSON fields
                summary['key_trends'] = json.loads(summary['key_trends'])
                summary['therapeutic_targets'] = json.loads(summary['therapeutic_targets'])
                summary['prognostic_markers'] = json.loads(summary['prognostic_markers'])
                return summary
            return None
    
    def get_summary_version(self) -> int:
        """Get current summary version"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = 'summary_version'")
            result = cursor.fetchone()
            return int(result[0]) if result else 0
