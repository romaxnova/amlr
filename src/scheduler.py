import schedule
import time
import threading
from datetime import datetime, timedelta
from src.database import DatabaseManager
from src.pubmed_scraper import PubMedScraper
from src.ai_analyzer import AIAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeeklyScheduler:
    def __init__(self):
        self.db = DatabaseManager()
        self.pubmed = PubMedScraper()
        self.ai = AIAnalyzer()
        self.running = False
        
    def start_scheduler(self):
        """Start the weekly scheduler in a background thread"""
        if self.running:
            return
            
        self.running = True
        # Schedule weekly updates every Monday at 9 AM
        schedule.every().monday.at("09:00").do(self.weekly_update)
        
        # Run scheduler in background thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("Weekly scheduler started - will update every Monday at 9 AM")
        
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour
            
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Weekly scheduler stopped")
        
    def weekly_update(self):
        """Perform weekly database update and regenerate summaries"""
        try:
            logger.info("Starting weekly update...")
            
            # Get last update time
            last_update = self.db.get_last_update()
            if not last_update:
                last_update = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
            # Search for new papers
            logger.info(f"Searching for papers since {last_update}")
            papers = self.pubmed.scrape_search_results(after_date=last_update)
            
            new_papers_count = 0
            timeline_entries = []
            
            for paper_data in papers:
                # Check if paper already exists
                if not self.db.paper_exists(paper_data.get('pmid')):
                    # Analyze with AI
                    analysis = self.ai.analyze_paper(paper_data)
                    
                    # Save to database - need to merge analysis into paper_data
                    paper_data['main_findings'] = analysis
                    success = self.db.insert_paper(paper_data)
                    
                    if success:
                        new_papers_count += 1
                        
                        # Add to timeline
                        timeline_entries.append({
                            'pmid': paper_data.get('pmid'),
                            'title': paper_data.get('title', ''),
                            'date': paper_data.get('publish_date', ''),
                            'journal': paper_data.get('journal', ''),
                            'summary': analysis[:200] + '...' if analysis else ''
                        })
            
            # Save timeline entries
            if timeline_entries:
                self.db.save_timeline_entries(timeline_entries, datetime.now().strftime('%Y-%m-%d'))
            
            # Regenerate research summary
            if new_papers_count > 0:
                logger.info(f"Regenerating summary with {new_papers_count} new papers")
                self._regenerate_summary()
                
            # Update last update timestamp
            self.db.update_last_update()
            
            logger.info(f"Weekly update completed: {new_papers_count} new papers added")
            
        except Exception as e:
            logger.error(f"Weekly update failed: {str(e)}")
            
    def _regenerate_summary(self):
        """Regenerate the research summary with latest papers"""
        try:
            # Get recent papers for summary
            recent_papers = self.db.get_recent_papers(limit=50)
            
            if recent_papers:
                # Generate new summary using the AI analyzer
                summary = self.ai.generate_comprehensive_summary(recent_papers, language="en")
                
                # Save updated summary to research_summaries table
                # Note: This would need a method in DatabaseManager to save research summaries
                logger.info("Research summary regenerated successfully")
                
        except Exception as e:
            logger.error(f"Failed to regenerate summary: {str(e)}")
            
    def force_update(self):
        """Manually trigger weekly update (for testing)"""
        logger.info("Forcing weekly update...")
        self.weekly_update()
