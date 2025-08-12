import sqlite3
import os
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
            # Initialize last update date if not exists
            cursor.execute('''
                INSERT OR IGNORE INTO settings (key, value) 
                VALUES ('last_update_date', '2024-08-12')
            ''')
            
            conn.commit()
    
    def insert_paper(self, paper_data: Dict) -> bool:
        """Insert or update a paper in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO papers 
                    (pmid, title, publish_date, article_type, num_references, 
                     main_findings, abstract, authors, journal, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    paper_data.get('pmid'),
                    paper_data.get('title'),
                    paper_data.get('publish_date'),
                    paper_data.get('article_type'),
                    paper_data.get('num_references'),
                    paper_data.get('main_findings'),
                    paper_data.get('abstract'),
                    paper_data.get('authors'),
                    paper_data.get('journal')
                ))
                conn.commit()
                return True
        except Exception as e:
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
