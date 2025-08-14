import os
from openai import OpenAI
from typing import List, Dict
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIAnalyzer:
    def __init__(self):
        try:
            api_key = os.getenv('XAI_API_KEY')
            if not api_key:
                raise ValueError("XAI_API_KEY not found in environment variables")
            
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            self.model = "grok-2"
            print("AI Analyzer initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize AI client: {e}")
            self.client = None
            self.model = None
    
    def analyze_paper(self, paper: Dict) -> str:
        """Analyze a single paper and extract main findings"""
        if not self.client:
            return "AI analysis unavailable"
            
        prompt = f"""
        Analyze the following research paper about AML (Acute Myeloid Leukemia) and TP53 mutations.
        Extract the main findings in a concise format using semicolon delimiters.
        Focus on clinical significance, molecular mechanisms, therapeutic implications, and prognostic factors.

        Title: {paper.get('title', 'N/A')}
        Abstract: {paper.get('abstract', 'N/A')}
        
        Provide main findings as a semicolon-separated list. Be concise but informative.
        Example format: "TP53 mutations found in 12% of AML patients; Associated with poor prognosis; Resistance to conventional chemotherapy; Potential target for MDM2 inhibitors"
        
        Main findings:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert hematologist and researcher specializing in AML and TP53 mutations. Provide concise, accurate medical insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error analyzing paper: {e}")
            return "Analysis failed"
    
    def generate_comprehensive_summary(self, papers: List[Dict], language: str = "en") -> str:
        """Generate a comprehensive summary of all research papers"""
        if not self.client:
            return "AI summary generation unavailable. Please check your XAI_API_KEY configuration."
        
        # Prepare data for summary
        findings_list = []
        for paper in papers:
            if paper.get('main_findings'):
                findings_list.append({
                    'title': paper.get('title', 'Unknown'),
                    'date': paper.get('publish_date', 'Unknown'),
                    'findings': paper.get('main_findings', ''),
                    'type': paper.get('article_type', 'Research Article')
                })
        
        language_prompts = {
            "en": "Generate a comprehensive research summary in English",
            "fr": "Générez un résumé de recherche complet en français", 
            "ru": "Создайте всеобъемлющий обзор исследований на русском языке"
        }
        
        language_instruction = language_prompts.get(language, language_prompts["en"])
        
        prompt = f"""
        {language_instruction} based on the following AML (Acute Myeloid Leukemia) and TP53 mutation research papers.

        Create a structured summary with the following sections:
        1. Executive Summary
        2. Key Clinical Findings
        3. Molecular Mechanisms
        4. Therapeutic Implications
        5. Prognostic Factors
        6. Emerging Trends
        7. Future Research Directions
        8. Methodology Overview

        Research Papers Data:
        {json.dumps(findings_list[:50], indent=2)}  # Limit to prevent token overflow

        Provide a detailed, well-structured summary that would be valuable for clinicians and researchers.
        Use markdown formatting for better readability.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert medical researcher and writer. Create comprehensive, accurate summaries in {language}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.4
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Summary generation failed"
    
    def extract_key_terms(self, paper: Dict) -> List[str]:
        """Extract key medical/research terms from a paper"""
        if not self.client:
            return []
            
        prompt = f"""
        Extract key medical and research terms from the following AML/TP53 research paper.
        Focus on: drugs, genes, proteins, pathways, techniques, biomarkers, and clinical terms.
        
        Title: {paper.get('title', 'N/A')}
        Abstract: {paper.get('abstract', 'N/A')}
        
        Provide a comma-separated list of important terms. Be precise and use standard nomenclature.
        Examples: TP53, MDM2, CPX-351, tetrandrine, mTOR, CRISPR, qPCR, overall survival
        
        Key terms:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a medical literature expert. Extract precise, standardized medical and research terms."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            terms_text = response.choices[0].message.content.strip()
            # Clean and split terms
            terms = [term.strip() for term in terms_text.split(',') if term.strip()]
            # Remove duplicates and normalize
            unique_terms = list(set([term for term in terms if len(term) > 1]))
            
            return unique_terms[:20]  # Limit to 20 terms
            
        except Exception as e:
            print(f"Error extracting key terms: {e}")
            return []
    
    def generate_incremental_summary(self, existing_summary: str, new_papers: List[Dict], 
                                   language: str = "en") -> str:
        """Generate an updated summary incorporating new papers"""
        if not self.client:
            return existing_summary
        
        # Extract findings from new papers
        new_findings = []
        for paper in new_papers:
            if paper.get('main_findings'):
                new_findings.append({
                    'title': paper.get('title', 'Unknown'),
                    'date': paper.get('publish_date', 'Unknown'),
                    'findings': paper.get('main_findings', ''),
                    'key_terms': paper.get('key_terms', [])
                })
        
        if not new_findings:
            return existing_summary
        
        language_prompts = {
            "en": "Update the research summary in English",
            "fr": "Mettez à jour le résumé de recherche en français", 
            "ru": "Обновите обзор исследований на русском языке"
        }
        
        language_instruction = language_prompts.get(language, language_prompts["en"])
        
        prompt = f"""
        {language_instruction} by incorporating the following new research findings into the existing comprehensive summary.

        EXISTING SUMMARY:
        {existing_summary}

        NEW RESEARCH FINDINGS TO INTEGRATE:
        {json.dumps(new_findings, indent=2)}

        Instructions:
        1. Integrate new findings into the appropriate sections
        2. Update statistics and trends
        3. Highlight any new therapeutic targets or biomarkers
        4. Maintain the existing structure and format
        5. Add a "Recent Updates" section if significant new information is found
        6. Keep the comprehensive nature while being concise

        Provide the updated complete summary in markdown format.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert medical researcher. Update summaries accurately in {language}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3500,
                temperature=0.4
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating incremental summary: {e}")
            return existing_summary

    def extract_research_trends(self, papers: List[Dict]) -> Dict:
        """Extract research trends and patterns"""
        
        findings_text = "\n".join([
            f"{paper.get('title', '')}: {paper.get('main_findings', '')}"
            for paper in papers if paper.get('main_findings')
        ])
        
        prompt = f"""
        Analyze the following AML/TP53 research findings and identify key trends, patterns, and emerging themes.
        
        Research Findings:
        {findings_text[:4000]}  # Limit text length
        
        Provide analysis in JSON format with the following structure:
        {{
            "key_trends": ["trend1", "trend2", "trend3"],
            "therapeutic_targets": ["target1", "target2"],
            "prognostic_markers": ["marker1", "marker2"],
            "research_gaps": ["gap1", "gap2"],
            "methodology_trends": ["method1", "method2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst specializing in medical literature. Provide structured analysis in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse JSON response
            trends_text = response.choices[0].message.content.strip()
            # Remove markdown code block formatting if present
            if "```json" in trends_text:
                trends_text = trends_text.split("```json")[1].split("```")[0]
            
            return json.loads(trends_text)
            
        except Exception as e:
            print(f"Error extracting trends: {e}")
            return {
                "key_trends": [],
                "therapeutic_targets": [],
                "prognostic_markers": [],
                "research_gaps": [],
                "methodology_trends": []
            }

    def generate_summary_for_papers(self, papers: List[Dict], language: str = "en") -> str:
        """Generate a focused summary for a specific set of papers (used for specialized summaries)"""
        if not self.client:
            return "AI summary generation unavailable. Please check your XAI_API_KEY configuration."
        
        if not papers:
            return "No papers provided for summary generation."
        
        # Prepare data for summary
        findings_list = []
        for paper in papers:
            findings_list.append({
                'title': paper.get('title', 'Unknown'),
                'date': paper.get('publish_date', 'Unknown'),
                'findings': paper.get('main_findings', ''),
                'abstract': paper.get('abstract', '')[:500],  # First 500 chars
                'type': paper.get('article_type', 'Research Article')
            })
        
        language_prompts = {
            "en": "Generate a focused research summary in English",
            "fr": "Générez un résumé de recherche ciblé en français", 
            "ru": "Создайте целевой обзор исследований на русском языке"
        }
        
        language_instruction = language_prompts.get(language, language_prompts["en"])
        
        prompt = f"""
        {language_instruction} based on the following {len(papers)} AML (Acute Myeloid Leukemia) and TP53 mutation research papers.

        Create a focused summary with the following sections:
        1. Overview of Selected Research
        2. Key Findings and Results
        3. Clinical Implications
        4. Molecular Mechanisms Identified
        5. Therapeutic Insights
        6. Prognostic Factors
        7. Research Limitations and Future Directions

        Research Papers Data:
        {json.dumps(findings_list, indent=2)}

        Provide a detailed, well-structured summary that synthesizes the findings from these specific papers.
        Use clear markdown formatting for better readability.
        Focus on the specific research themes represented in this paper set.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an expert medical researcher and writer. Create focused, accurate summaries in {language} for specific research paper sets."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.4
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating specialized summary: {e}")
            return f"Summary generation failed: {str(e)}"

    def generate_specialized_summary(self, papers: List[Dict], focus_terms: List[str], 
                                   language: str = "en", summary_name: str = "") -> str:
        """Generate a focused, factual summary about specific key terms"""
        if not papers:
            return "No papers provided for analysis."
        
        if not focus_terms:
            return "No focus terms provided for specialized analysis."
        
        if not self.client:
            return "AI service not available."
        
        # Prepare relevant paper data
        relevant_papers = []
        for paper in papers:
            # Extract key facts about this paper
            relevant_papers.append({
                'title': paper.get('title', ''),
                'authors': paper.get('authors', '').split(',')[0] + ' et al.' if paper.get('authors') else 'Unknown',
                'journal': paper.get('journal', ''),
                'year': paper.get('publish_date', '')[:4] if paper.get('publish_date') else 'Unknown',
                'findings': paper.get('main_findings', ''),
                'type': paper.get('article_type', 'Research')
            })
        
        # Language-specific prompts for concise, factual summaries
        language_prompts = {
            "en": {
                "instruction": "Create a concise, factual summary in English about",
                "format": "Write a brief factual summary focusing exclusively on"
            },
            "fr": {
                "instruction": "Créez un résumé factuel et concis en français sur",
                "format": "Rédigez un bref résumé factuel portant exclusivement sur"
            },
            "ru": {
                "instruction": "Создайте краткий фактический обзор на русском языке о",
                "format": "Напишите краткий фактический обзор, сосредоточенный исключительно на"
            }
        }
        
        lang_config = language_prompts.get(language, language_prompts["en"])
        focus_terms_native = focus_terms  # Terms can be translated in the AI response
        
        prompt = f"""
        {lang_config['format']} {', '.join(focus_terms_native)} in acute myeloid leukemia research.

        Analyze these {len(papers)} research papers and create a brief, factual summary about {', '.join(focus_terms_native)}.

        Papers to analyze:
        {json.dumps(relevant_papers, indent=2)}

        REQUIREMENTS:
        1. Write ONLY about {', '.join(focus_terms_native)} - ignore unrelated content
        2. Be factual and concise - no lengthy introductions or conclusions
        3. Translate the key terms to the target language naturally
        4. Focus on: what these terms are, key research findings, clinical relevance
        5. Use simple paragraphs, not formal sections
        6. Mention specific studies when relevant (Author, Year, Journal)
        7. Maximum 400 words

        Format: 
        - Brief definition/context of the focus terms
        - Key findings from the research papers about these terms
        - Clinical significance or implications
        - Current research status

        Do NOT include:
        - General AML background
        - Lengthy methodology descriptions  
        - Formal section headers
        - Repetitive content
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a medical research expert. Write concise, factual summaries about specific topics. Focus only on the requested terms. Use the target language naturally."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,  # Reduced for conciseness
                temperature=0.2  # Lower for more factual content
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating specialized summary: {e}")
            return f"Error generating summary: {str(e)}"
