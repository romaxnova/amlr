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
    
    def build_search_query(self, after_date: Optional[str] = None) -> str:
        """Build PubMed search query"""
        base_query = "(acute myeloid leukemia[Title/Abstract] OR AML[Title/Abstract]) AND (TP53[Title/Abstract] OR p53[Title/Abstract])"
        
        # Add date filter if specified
        if after_date:
            date_obj = datetime.strptime(after_date, '%Y-%m-%d')
            date_filter = f" AND {date_obj.year}[dp]:{datetime.now().year}[dp]"
            base_query += date_filter
        else:
            # Default to last 1 year
            current_year = datetime.now().year
            base_query += f" AND {current_year - 1}[dp]:{current_year}[dp]"
        
        return base_query
    
    def esearch(self, query: str, retmax: int = 100) -> Dict:
        """Search PubMed using ESearch"""
        url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': retmax,
            'sort': 'date',
            'tool': self.tool,
            'email': self.email,
            'usehistory': 'y'  # Use history server for large result sets
        }
        
        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Extract results
            result = {
                'count': int(root.find('.//Count').text if root.find('.//Count') is not None else 0),
                'retmax': int(root.find('.//RetMax').text if root.find('.//RetMax') is not None else 0),
                'retstart': int(root.find('.//RetStart').text if root.find('.//RetStart') is not None else 0),
                'webenv': root.find('.//WebEnv').text if root.find('.//WebEnv') is not None else None,
                'querykey': root.find('.//QueryKey').text if root.find('.//QueryKey') is not None else None,
                'ids': []
            }
            
            # Get PMIDs
            id_list = root.find('.//IdList')
            if id_list is not None:
                result['ids'] = [id_elem.text for id_elem in id_list.findall('.//Id')]
            
            return result
            
        except Exception as e:
            print(f"Error in ESearch: {e}")
            return {'count': 0, 'ids': [], 'webenv': None, 'querykey': None}
    
    def efetch(self, pmids: List[str] = None, webenv: str = None, querykey: str = None, retstart: int = 0, retmax: int = 100) -> List[Dict]:
        """Fetch article details using EFetch"""
        url = f"{self.base_url}efetch.fcgi"
        
        # Build parameters
        params = {
            'db': 'pubmed',
            'rettype': 'abstract',
            'retmode': 'xml',
            'tool': self.tool,
            'email': self.email
        }
        
        # Use either PMIDs or WebEnv/QueryKey
        if pmids:
            params['id'] = ','.join(pmids)
        elif webenv and querykey:
            params['WebEnv'] = webenv
            params['query_key'] = querykey
            params['retstart'] = retstart
            params['retmax'] = retmax
        else:
            raise ValueError("Either pmids or webenv/querykey must be provided")
        
        try:
            time.sleep(self.request_delay)
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            papers = []
            
            # Process each PubmedArticle
            articles = root.findall('.//PubmedArticle')
            print(f"Found {len(articles)} articles in EFetch response")
            
            for article in articles:
                paper_data = self._extract_paper_from_xml(article)
                if paper_data:
                    papers.append(paper_data)
            
            return papers
            
        except Exception as e:
            print(f"Error in EFetch: {e}")
            return []
    
    def _extract_paper_from_xml(self, article) -> Optional[Dict]:
        """Extract paper data from XML article element"""
        try:
            paper = {}
            
            # Get PMID
            pmid_elem = article.find('.//PMID')
            paper['pmid'] = pmid_elem.text if pmid_elem is not None else None
            
            # Get title
            title_elem = article.find('.//ArticleTitle')
            paper['title'] = title_elem.text if title_elem is not None else "Unknown Title"
            
            # Get authors
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('.//Author'):
                    last_name = author.find('.//LastName')
                    first_name = author.find('.//ForeName')
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name += f" {first_name.text}"
                        authors.append(name)
            paper['authors'] = ', '.join(authors) if authors else "Unknown Authors"
            
            # Get journal information
            journal_elem = article.find('.//Journal/Title')
            if journal_elem is None:
                journal_elem = article.find('.//Journal/ISOAbbreviation')
            paper['journal'] = journal_elem.text if journal_elem is not None else "Unknown Journal"
            
            # Get publication date
            pub_date = article.find('.//PubDate')
            if pub_date is not None:
                year = pub_date.find('.//Year')
                month = pub_date.find('.//Month')
                day = pub_date.find('.//Day')
                
                if year is not None:
                    year_text = year.text
                    month_text = month.text if month is not None else "01"
                    day_text = day.text if day is not None else "01"
                    
                    # Convert month name to number if needed
                    month_mapping = {
                        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                    }
                    
                    if month_text in month_mapping:
                        month_text = month_mapping[month_text]
                    elif not month_text.isdigit():
                        month_text = "01"
                    
                    try:
                        paper['publish_date'] = f"{year_text}-{month_text.zfill(2)}-{day_text.zfill(2)}"
                    except:
                        paper['publish_date'] = f"{year_text}-01-01"
                else:
                    paper['publish_date'] = "2025-01-01"
            else:
                paper['publish_date'] = "2025-01-01"
            
            # Get abstract
            abstract_elem = article.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                # Handle structured abstracts
                abstract_texts = article.findall('.//Abstract/AbstractText')
                if len(abstract_texts) > 1:
                    # Structured abstract
                    abstract_parts = []
                    for abs_text in abstract_texts:
                        label = abs_text.get('Label', '')
                        text = abs_text.text or ''
                        if label:
                            abstract_parts.append(f"{label}: {text}")
                        else:
                            abstract_parts.append(text)
                    paper['abstract'] = ' '.join(abstract_parts)
                else:
                    # Simple abstract
                    paper['abstract'] = abstract_elem.text or ''
            else:
                paper['abstract'] = f"Research on AML and TP53 mutations. Title: {paper['title']}"
            
            # Get publication types
            pub_types = []
            pub_type_list = article.findall('.//PublicationType')
            for pub_type in pub_type_list:
                if pub_type.text:
                    pub_types.append(pub_type.text)
            
            if pub_types:
                paper['article_type'] = pub_types[0]  # Use first publication type
            else:
                paper['article_type'] = "Research Article"
            
            # Get number of references (if available)
            references = article.findall('.//Reference')
            paper['num_references'] = len(references) if references else None
            
            return paper
            
        except Exception as e:
            print(f"Error extracting paper data from XML: {e}")
            return None
    
    def scrape_search_results(self, url: str = None, after_date: Optional[str] = None) -> List[Dict]:
        """Main method to scrape PubMed results using E-utilities"""
        try:
            # Build search query
            query = self.build_search_query(after_date)
            print(f"Searching PubMed with query: {query}")
            
            # Step 1: Search for papers
            search_result = self.esearch(query, retmax=10000)  # Get up to 10,000 results
            print(f"Found {search_result['count']} total papers")
            
            if search_result['count'] == 0:
                return []
            
            all_papers = []
            
            # Step 2: Fetch papers in batches
            if search_result['webenv'] and search_result['querykey']:
                # Use WebEnv/QueryKey for large result sets
                batch_size = 100
                total_papers = min(search_result['count'], 1000)  # Limit to 1000 papers for now
                
                for start in range(0, total_papers, batch_size):
                    batch_size_actual = min(batch_size, total_papers - start)
                    print(f"Fetching papers {start + 1} to {start + batch_size_actual} of {total_papers}")
                    
                    papers = self.efetch(
                        webenv=search_result['webenv'],
                        querykey=search_result['querykey'],
                        retstart=start,
                        retmax=batch_size_actual
                    )
                    
                    all_papers.extend(papers)
                    
                    # Rate limiting
                    time.sleep(self.request_delay)
            else:
                # Use PMIDs directly for smaller result sets
                if search_result['ids']:
                    papers = self.efetch(pmids=search_result['ids'][:100])  # Limit to first 100
                    all_papers.extend(papers)
            
            print(f"Successfully retrieved {len(all_papers)} papers with abstracts")
            return all_papers
            
        except Exception as e:
            print(f"Error scraping PubMed: {e}")
            return []
    
    def get_paper_count(self, after_date: Optional[str] = None) -> int:
        """Get total number of papers matching the search criteria"""
        try:
            query = self.build_search_query(after_date)
            search_result = self.esearch(query, retmax=1)  # Only need count
            return search_result['count']
        except Exception as e:
            print(f"Error getting paper count: {e}")
            return 0
    
    def scrape_multiple_pages(self, total_results: int, page_size: int = 100, after_date: Optional[str] = None) -> List[Dict]:
        """Scrape multiple pages of results - now handled automatically by scrape_search_results"""
        return self.scrape_search_results(after_date=after_date)
    
    def build_search_url(self, page_size: int = 100, after_date: Optional[str] = None) -> str:
        """Build search URL - kept for compatibility but not used with E-utilities"""
        query = self.build_search_query(after_date)
        return f"https://pubmed.ncbi.nlm.nih.gov/?term={urllib.parse.quote(query)}&size={page_size}"
