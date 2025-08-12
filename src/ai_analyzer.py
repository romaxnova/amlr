import os
from openai import OpenAI
from typing import List, Dict
import json

class AIAnalyzer:
    def __init__(self):
        try:
            self.client = OpenAI(
                api_key=os.getenv('XAI_API_KEY'),
                base_url="https://api.x.ai/v1"
            )
            self.model = "grok-beta"
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
