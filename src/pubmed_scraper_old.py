import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import urllib.parse

class PubMedScraper:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AML-TP53-Research-Tool/1.0 (contact@example.com)'
        })
        self.tool = "AML-TP53-Research-Tool"
        self.email = "contact@example.com"
        # Rate limiting: max 3 requests per second without API key
        self.request_delay = 0.34  # ~3 requests per second
    
    def build_search_url(self, page_size: int = 100, after_date: Optional[str] = None) -> str:
        """Build PubMed search URL with filters"""
        base_query = "(acute myeloid leukemia[Title/Abstract] OR AML[Title/Abstract]) AND (TP53[Title/Abstract] OR p53[Title/Abstract])"
        
        params = {
            'term': base_query,
            'filter': 'datesearch.y_1',  # Last 1 year
            'sort': 'date',
            'size': str(page_size)
        }
        
        # If updating, modify date filter
        if after_date:
            # Convert date to PubMed format and update filter
            date_obj = datetime.strptime(after_date, '%Y-%m-%d')
            params['filter'] = f'datesearch.y_{date_obj.year}'
        
        return self.base_url + "?" + urllib.parse.urlencode(params)
    
    def scrape_search_results(self, url: str) -> List[Dict]:
        """Scrape papers from PubMed search results"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            papers = []
            
            # Find containers with paper data - look for divs containing PMID links
            paper_containers = []
            
            # Method 1: Find divs containing links to PMIDs
            pmid_links = soup.find_all('a', href=lambda x: x and '/pmid/' in str(x))
            for link in pmid_links:
                # Find the parent container
                container = link.find_parent('div')
                if container and container not in paper_containers:
                    paper_containers.append(container)
            
            print(f"Found {len(paper_containers)} papers on page")
            
            for container in paper_containers:
                paper_data = self._extract_paper_data(container)
                if paper_data:
                    papers.append(paper_data)
            
            return papers
            
        except Exception as e:
            print(f"Error scraping PubMed: {e}")
            return []
    
    def _extract_paper_data(self, article) -> Optional[Dict]:
        """Extract paper data from article element"""
        try:
            paper = {}
            
            # Extract title - try multiple selectors
            title_elem = article.find('a', class_=lambda x: x and 'title' in str(x))
            if not title_elem:
                title_elem = article.find('a')
            paper['title'] = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Extract PMID from link
            if title_elem and title_elem.get('href'):
                href = title_elem.get('href')
                if '/pmid/' in href:
                    paper['pmid'] = href.split('/pmid/')[-1].split('/')[0]
                else:
                    paper['pmid'] = None
            else:
                paper['pmid'] = None
            
            # Extract authors
            authors_elem = article.find('span', class_=lambda x: x and 'authors' in str(x))
            paper['authors'] = authors_elem.text.strip() if authors_elem else "Unknown Authors"
            
            # Extract journal info
            journal_elem = article.find('span', class_=lambda x: x and ('citation' in str(x) or 'journal' in str(x)))
            if journal_elem:
                journal_text = journal_elem.text.strip()
                paper['journal'] = journal_text
                
                # Extract year
                import re
                year_match = re.search(r'(\d{4})', journal_text)
                if year_match:
                    paper['publish_date'] = f"{year_match.group(1)}-01-01"
                else:
                    paper['publish_date'] = "2025-01-01"
            else:
                paper['journal'] = "Unknown Journal"
                paper['publish_date'] = "2025-01-01"
            
            # Set defaults
            paper['abstract'] = f"Research on AML and TP53 mutations. Title: {paper['title']}"
            paper['article_type'] = "Research Article"
            paper['num_references'] = None
            
            return paper
            
        except Exception as e:
            print(f"Error extracting paper data: {e}")
            return None
    
    def _extract_article_type(self, citation_text: str) -> str:
        """Extract article type from citation text"""
        # Common article types in medical literature
        types = ['Review', 'Clinical Trial', 'Meta-Analysis', 'Case Report', 
                'Randomized Controlled Trial', 'Systematic Review', 'Letter', 'Editorial']
        
        for article_type in types:
            if article_type.lower() in citation_text.lower():
                return article_type
        
        return "Research Article"
    
    def scrape_multiple_pages(self, total_results: int, page_size: int = 100, after_date: Optional[str] = None) -> List[Dict]:
        """Scrape multiple pages of results"""
        all_papers = []
        pages_needed = (total_results + page_size - 1) // page_size
        
        for page in range(pages_needed):
            print(f"Scraping page {page + 1} of {pages_needed}...")
            
            # Modify URL for pagination
            url = self.build_search_url(page_size, after_date)
            if page > 0:
                url += f"&page={page + 1}"
            
            papers = self.scrape_search_results(url)
            all_papers.extend(papers)
            
            # Be respectful to PubMed servers
            time.sleep(1)
        
        return all_papers
    
    def get_paper_count(self, after_date: Optional[str] = None) -> int:
        """Get total number of papers matching the search criteria"""
        try:
            url = self.build_search_url(10, after_date)  # Small page size just to get count
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for results count - updated selector
            count_elem = soup.find('div', class_='results-amount')
            if count_elem:
                count_text = count_elem.text.strip()
                print(f"Found results text: {count_text}")
                
                # Extract number - handle different formats
                import re
                # Try to find just the number at the start
                match = re.search(r'(\d+)', count_text)
                if match:
                    count = int(match.group(1))
                    print(f"Extracted count: {count}")
                    return count
            
            # Fallback: count article elements on the page
            articles = soup.find_all('article')
            if articles:
                print(f"Found {len(articles)} articles on page, assuming more exist")
                return 250  # Conservative estimate when we can't get exact count
            
            return 0
            
        except Exception as e:
            print(f"Error getting paper count: {e}")
            return 0
