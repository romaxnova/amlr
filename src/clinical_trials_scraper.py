import requests
import feedparser
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClinicalTrialsScraper:
    def __init__(self):
        self.base_rss_url = "https://clinicaltrials.gov/ct2/results/rss.xml"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_trials(self, key_terms: List[str], days_back: int = 7) -> List[Dict]:
        """
        Search for clinical trials related to AML and key terms
        """
        all_trials = []
        
        # Base AML searches
        base_queries = [
            "acute myeloid leukemia",
            "AML", 
            "TP53 mutation"
        ]
        
        # Combine with key terms
        search_terms = base_queries + key_terms[:10]  # Limit to prevent too many requests
        
        for term in search_terms:
            try:
                trials = self._search_single_term(term, days_back)
                all_trials.extend(trials)
                logger.info(f"Found {len(trials)} trials for term: {term}")
            except Exception as e:
                logger.error(f"Error searching for term '{term}': {str(e)}")
                continue
        
        # Remove duplicates based on NCT ID
        unique_trials = {}
        for trial in all_trials:
            nct_id = trial.get('nct_id')
            if nct_id and nct_id not in unique_trials:
                unique_trials[nct_id] = trial
        
        return list(unique_trials.values())
    
    def _search_single_term(self, term: str, days_back: int) -> List[Dict]:
        """Search for a single term in clinical trials"""
        try:
            # Build RSS URL with search parameters
            params = {
                'term': term,
                'type': 'Intr',  # Interventional studies
                'rslt': 'Without',  # Without results (ongoing/recruiting)
                'age_v': '&age=1',  # Adult studies
                'rcv_s': self._get_date_filter(days_back),
                'count': '50'  # Limit results
            }
            
            # Construct URL
            param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"{self.base_rss_url}?{param_string}"
            
            logger.info(f"Searching ClinicalTrials.gov RSS for: {term}")
            
            # Parse RSS feed
            feed = feedparser.parse(url)
            
            trials = []
            for entry in feed.entries:
                trial = self._parse_trial_entry(entry, term)
                if trial:
                    trials.append(trial)
            
            return trials
            
        except Exception as e:
            logger.error(f"Error searching for term '{term}': {str(e)}")
            return []
    
    def _parse_trial_entry(self, entry, search_term: str) -> Optional[Dict]:
        """Parse a single trial entry from RSS feed"""
        try:
            # Extract NCT ID from link
            nct_id = None
            if hasattr(entry, 'link'):
                nct_match = re.search(r'NCT\d+', entry.link)
                if nct_match:
                    nct_id = nct_match.group()
            
            # Extract basic information
            title = getattr(entry, 'title', 'Unknown Trial')
            summary = getattr(entry, 'summary', '')
            link = getattr(entry, 'link', '')
            published = getattr(entry, 'published', '')
            
            # Parse published date
            published_date = None
            if published:
                try:
                    published_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
                except:
                    published_date = datetime.now().strftime('%Y-%m-%d')
            
            # Extract phase and status from summary
            phase = self._extract_phase(summary)
            status = self._extract_status(summary)
            
            # Check relevance to AML/TP53
            relevance_score = self._calculate_relevance(title, summary, search_term)
            
            if relevance_score > 0.3:  # Only include relevant trials
                return {
                    'nct_id': nct_id,
                    'title': title,
                    'summary': summary[:500] + '...' if len(summary) > 500 else summary,
                    'link': link,
                    'published_date': published_date,
                    'phase': phase,
                    'status': status,
                    'search_term': search_term,
                    'relevance_score': relevance_score,
                    'source': 'clinicaltrials.gov'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing trial entry: {str(e)}")
            return None
    
    def _extract_phase(self, text: str) -> str:
        """Extract study phase from text"""
        phase_patterns = [
            r'Phase\s+(\d+(?:/\d+)?)',
            r'Phase\s+([IVX]+)',
        ]
        
        for pattern in phase_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"Phase {match.group(1)}"
        
        if re.search(r'early\s+phase', text, re.IGNORECASE):
            return "Early Phase"
        
        return "Unknown Phase"
    
    def _extract_status(self, text: str) -> str:
        """Extract study status from text"""
        status_keywords = {
            'recruiting': 'Recruiting',
            'active': 'Active',
            'enrolling': 'Enrolling',
            'completed': 'Completed',
            'terminated': 'Terminated',
            'suspended': 'Suspended',
            'withdrawn': 'Withdrawn'
        }
        
        text_lower = text.lower()
        for keyword, status in status_keywords.items():
            if keyword in text_lower:
                return status
        
        return "Unknown Status"
    
    def _calculate_relevance(self, title: str, summary: str, search_term: str) -> float:
        """Calculate relevance score for AML/TP53 research"""
        text = (title + ' ' + summary).lower()
        score = 0.0
        
        # High relevance terms
        high_terms = ['aml', 'acute myeloid leukemia', 'tp53', 'p53', 'myeloid']
        for term in high_terms:
            if term in text:
                score += 0.3
        
        # Medium relevance terms  
        medium_terms = ['leukemia', 'cancer', 'oncology', 'hematology', 'mutation']
        for term in medium_terms:
            if term in text:
                score += 0.2
        
        # Drug terms from our research
        drug_terms = ['venetoclax', 'azacitidine', 'decitabine', 'cytarabine', 'daunorubicin']
        for term in drug_terms:
            if term in text:
                score += 0.4
        
        # Search term relevance
        if search_term.lower() in text:
            score += 0.2
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _get_date_filter(self, days_back: int) -> str:
        """Get date filter for RSS search"""
        date_from = (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y')
        return date_from
    
    def get_trial_details(self, nct_id: str) -> Dict:
        """Get detailed information for a specific trial"""
        try:
            # Use ClinicalTrials.gov API for detailed info
            api_url = f"https://clinicaltrials.gov/api/query/full_studies?expr={nct_id}&fmt=json"
            
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('FullStudiesResponse', {}).get('FullStudies'):
                study = data['FullStudiesResponse']['FullStudies'][0]['Study']
                
                return {
                    'nct_id': nct_id,
                    'title': study.get('ProtocolSection', {}).get('IdentificationModule', {}).get('BriefTitle', ''),
                    'official_title': study.get('ProtocolSection', {}).get('IdentificationModule', {}).get('OfficialTitle', ''),
                    'summary': study.get('ProtocolSection', {}).get('DescriptionModule', {}).get('BriefSummary', ''),
                    'detailed_description': study.get('ProtocolSection', {}).get('DescriptionModule', {}).get('DetailedDescription', ''),
                    'phase': study.get('ProtocolSection', {}).get('DesignModule', {}).get('PhaseList', {}).get('Phase', ['Unknown'])[0],
                    'status': study.get('ProtocolSection', {}).get('StatusModule', {}).get('OverallStatus', 'Unknown'),
                    'start_date': study.get('ProtocolSection', {}).get('StatusModule', {}).get('StartDateStruct', {}).get('StartDate', ''),
                    'completion_date': study.get('ProtocolSection', {}).get('StatusModule', {}).get('CompletionDateStruct', {}).get('CompletionDate', ''),
                    'sponsor': study.get('ProtocolSection', {}).get('SponsorCollaboratorsModule', {}).get('LeadSponsor', {}).get('LeadSponsorName', ''),
                    'location_countries': study.get('ProtocolSection', {}).get('ContactsLocationsModule', {}).get('LocationList', {}).get('Location', []),
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting trial details for {nct_id}: {str(e)}")
            return {}
