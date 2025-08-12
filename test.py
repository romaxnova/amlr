#!/usr/bin/env python3
"""
Test script for AML Research Tool
Tests core functionality without requiring API keys
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append('src')

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from database import DatabaseManager
        print("✅ Database module imported successfully")
        
        from pubmed_scraper import PubMedScraper
        print("✅ PubMed scraper module imported successfully")
        
        from export_manager import ExportManager
        print("✅ Export manager module imported successfully")
        
        # Skip AI analyzer test if no API key
        if os.getenv('XAI_API_KEY'):
            from ai_analyzer import AIAnalyzer
            print("✅ AI analyzer module imported successfully")
        else:
            print("⚠️  Skipping AI analyzer test (no API key)")
            
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from database import DatabaseManager
        
        # Use test database
        db = DatabaseManager("./data/test.db")
        
        # Test paper insertion
        test_paper = {
            'pmid': 'TEST123',
            'title': 'Test Paper on AML and TP53',
            'authors': 'Test Author et al.',
            'journal': 'Test Journal',
            'publish_date': '2025-08-12',
            'article_type': 'Research Article',
            'main_findings': 'Test finding 1; Test finding 2',
            'abstract': 'This is a test abstract for testing purposes.'
        }
        
        success = db.insert_paper(test_paper)
        if success:
            print("✅ Paper insertion successful")
        else:
            print("❌ Paper insertion failed")
            return False
        
        # Test paper retrieval
        papers = db.get_all_papers(limit=1)
        if papers and len(papers) > 0:
            print("✅ Paper retrieval successful")
        else:
            print("❌ Paper retrieval failed")
            return False
        
        # Test stats
        stats = db.get_stats()
        if stats and 'total_papers' in stats:
            print("✅ Statistics generation successful")
        else:
            print("❌ Statistics generation failed")
            return False
        
        # Clean up test database
        import sqlite3
        if os.path.exists("./data/test.db"):
            os.remove("./data/test.db")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_scraper():
    """Test PubMed scraper functionality"""
    print("\nTesting PubMed scraper...")
    
    try:
        from pubmed_scraper import PubMedScraper
        
        scraper = PubMedScraper()
        
        # Test URL building
        url = scraper.build_search_url(10)
        if 'pubmed.ncbi.nlm.nih.gov' in url:
            print("✅ URL building successful")
        else:
            print("❌ URL building failed")
            return False
        
        # Note: We won't test actual scraping to avoid hitting PubMed servers during tests
        print("✅ Scraper module functional (actual scraping not tested)")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper test error: {e}")
        return False

def test_export():
    """Test export functionality"""
    print("\nTesting export manager...")
    
    try:
        from export_manager import ExportManager
        
        exporter = ExportManager("./exports_test")
        
        # Test CSV export
        test_papers = [
            {
                'title': 'Test Paper 1',
                'authors': 'Author 1',
                'journal': 'Journal 1',
                'publish_date': '2025-01-01',
                'pmid': 'TEST1'
            },
            {
                'title': 'Test Paper 2', 
                'authors': 'Author 2',
                'journal': 'Journal 2',
                'publish_date': '2025-01-02',
                'pmid': 'TEST2'
            }
        ]
        
        csv_file = exporter.export_to_csv(test_papers, "test_export.csv")
        if os.path.exists(csv_file):
            print("✅ CSV export successful")
            # Clean up
            os.remove(csv_file)
            if os.path.exists("./exports_test"):
                os.rmdir("./exports_test")
        else:
            print("❌ CSV export failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Export test error: {e}")
        return False

def test_flask_app():
    """Test Flask app can be imported and configured"""
    print("\nTesting Flask application...")
    
    try:
        # Set test environment
        os.environ['FLASK_SECRET_KEY'] = 'test-key'
        
        from app import app
        
        # Test app configuration
        if app.secret_key:
            print("✅ Flask app configuration successful")
        else:
            print("❌ Flask app configuration failed")
            return False
        
        # Test that routes are registered
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = ['/', '/update_research', '/generate_summary', '/browse']
        
        for route in expected_routes:
            if route in rules:
                print(f"✅ Route {route} registered")
            else:
                print(f"❌ Route {route} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧬 AML Research Tool - Test Suite")
    print("==================================")
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    
    tests = [
        test_imports,
        test_database,
        test_scraper,
        test_export,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nNext steps:")
        print("1. Add your XAI_API_KEY to .env file")
        print("2. Run: python run.py --init")
        print("3. Run: python run.py")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
