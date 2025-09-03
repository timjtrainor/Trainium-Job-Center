"""
CrewAI-inspired job review service for multi-agent job analysis.

This service implements a multi-agent approach to job review, where different
specialized "agents" analyze various aspects of job postings to provide
comprehensive insights and recommendations.
"""
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from loguru import logger
from crewai import Crew, Process, crew

from ..models.jobspy import ScrapedJob
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .evaluation_pipeline import Task


class SkillsAnalysisAgent:
    """Agent specialized in analyzing job skills and requirements."""
    
    def __init__(self, llm_router=None, web_search=None):
        """Initialize agent with optional LLM and web search capabilities."""
        self.llm_router = llm_router
        self.web_search = web_search
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze skills and requirements from job description."""
        description = job.get('description', '') if isinstance(job, dict) else (job.description or '')
        title = job.get('title', '') if isinstance(job, dict) else (job.title or '')
        company = job.get('company', '') if isinstance(job, dict) else (job.company or '')
        
        # Use LLM for intelligent skills analysis if available
        if self.llm_router:
            try:
                return self._analyze_with_llm(title, company, description)
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based analysis
        return self._analyze_rule_based(title, description)
    
    def _analyze_with_llm(self, title: str, company: str, description: str) -> Dict[str, Any]:
        """Use LLM for intelligent skills analysis."""
        prompt = f"""
Analyze the following job posting and extract information about skills and requirements:

Job Title: {title}
Company: {company}
Job Description: {description}

Please provide analysis in the following format:
1. Required technical skills (list)
2. Preferred technical skills (list)
3. Experience level (Entry-Level, Mid-Level, Senior, Executive)
4. Education requirements (High School, Bachelor's, Master's, PhD, Not Specified)
5. Soft skills mentioned (list)

Be concise and focus on the most relevant skills mentioned.
"""
        
        response = self.llm_router.generate(prompt, max_tokens=500, temperature=0.3)
        
        # Parse LLM response (simplified parsing - in production would be more robust)
        return self._parse_llm_response(response, description)
    
    def _parse_llm_response(self, response: str, description: str) -> Dict[str, Any]:
        """Parse LLM response and combine with rule-based analysis."""
        # For now, combine LLM insights with rule-based fallbacks
        rule_based = self._analyze_rule_based("", description)
        
        # Extract insights from LLM response
        response_lower = response.lower()
        
        # Determine experience level from LLM response
        if any(term in response_lower for term in ['senior', 'lead', 'principal', 'executive']):
            experience_level = 'Senior'
        elif any(term in response_lower for term in ['mid-level', 'intermediate', 'experienced']):
            experience_level = 'Mid-Level'
        elif any(term in response_lower for term in ['entry', 'junior', 'graduate']):
            experience_level = 'Entry-Level'
        else:
            experience_level = rule_based['experience_level']
        
        return {
            'required_skills': rule_based['required_skills'],  # Combine with LLM parsing in production
            'preferred_skills': rule_based['preferred_skills'],
            'experience_level': experience_level,
            'education_requirements': rule_based['education_requirements'],
            'all_technical_skills': rule_based['all_technical_skills'],
            'llm_insights': response[:200]  # Store first 200 chars of LLM analysis
        }
    
    def _analyze_rule_based(self, title: str, description: str) -> Dict[str, Any]:
        """Fallback rule-based analysis."""
        # Common technical skills patterns
        tech_skills = self._extract_technical_skills(description + ' ' + title)
        
        # Experience level analysis
        experience_level = self._determine_experience_level(description)
        
        # Education requirements
        education = self._extract_education_requirements(description)
        
        # Separate required vs preferred skills
        required_skills, preferred_skills = self._categorize_skills(description, tech_skills)
        
        return {
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'experience_level': experience_level,
            'education_requirements': education,
            'all_technical_skills': tech_skills
        }
    
    def _extract_technical_skills(self, text: str) -> List[str]:
        """Extract technical skills from job text."""
        text_lower = text.lower()
        
        # Common technical skills to look for
        skills_patterns = {
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust', 'scala', 'kotlin',
            'php', 'ruby', 'swift', 'objective-c', 'r', 'matlab', 'perl', 'shell', 'bash',
            
            # Web technologies
            'react', 'angular', 'vue.js', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
            'html', 'css', 'sass', 'less', 'webpack', 'babel', 'npm', 'yarn',
            
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb',
            'sqlite', 'oracle', 'sql server', 'nosql',
            
            # Cloud & Infrastructure
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'terraform', 'ansible',
            'jenkins', 'gitlab', 'github actions', 'circleci', 'travis ci',
            
            # Data & ML
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'spark', 'hadoop',
            'jupyter', 'tableau', 'power bi', 'sql', 'etl', 'data pipeline',
            
            # Other tools
            'git', 'jira', 'confluence', 'slack', 'linux', 'unix', 'vim', 'vscode', 'intellij'
        }
        
        found_skills = []
        for skill in skills_patterns:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return list(set(found_skills))
    
    def _determine_experience_level(self, description: str) -> str:
        """Determine experience level from job description."""
        desc_lower = description.lower()
        
        # Senior level indicators
        if any(term in desc_lower for term in ['senior', 'lead', 'principal', 'staff', 'architect', '7+ years', '8+ years', '10+ years']):
            return 'Senior'
        
        # Mid level indicators
        if any(term in desc_lower for term in ['3+ years', '4+ years', '5+ years', '6+ years', 'experienced']):
            return 'Mid-Level'
        
        # Entry level indicators
        if any(term in desc_lower for term in ['junior', 'entry', 'graduate', 'new grad', '0-2 years', '1-2 years']):
            return 'Entry-Level'
        
        return 'Not Specified'
    
    def _extract_education_requirements(self, description: str) -> str:
        """Extract education requirements."""
        desc_lower = description.lower()
        
        if 'phd' in desc_lower or 'doctorate' in desc_lower:
            return 'PhD/Doctorate'
        elif 'master' in desc_lower or 'mba' in desc_lower:
            return 'Master\'s Degree'
        elif 'bachelor' in desc_lower or 'degree' in desc_lower:
            return 'Bachelor\'s Degree'
        elif 'high school' in desc_lower or 'diploma' in desc_lower:
            return 'High School'
        
        return 'Not Specified'
    
    def _categorize_skills(self, description: str, all_skills: List[str]) -> tuple:
        """Categorize skills as required or preferred."""
        desc_lower = description.lower()
        
        required_skills = []
        preferred_skills = []
        
        for skill in all_skills:
            skill_lower = skill.lower()
            
            # Look for required indicators around the skill
            if any(req in desc_lower for req in [f'required {skill_lower}', f'{skill_lower} required', 'must have', 'essential']):
                required_skills.append(skill)
            elif any(pref in desc_lower for pref in [f'preferred {skill_lower}', f'{skill_lower} preferred', 'nice to have', 'bonus']):
                preferred_skills.append(skill)
            else:
                # Default to required if not clearly categorized
                required_skills.append(skill)
        
        return required_skills, preferred_skills


def build_skills_task(job: Dict[str, Any]) -> "Task":
    """Create a task that runs the SkillsAnalysisAgent."""
    from .evaluation_pipeline import Task  # Local import to avoid circular dependency

    async def _run() -> Dict[str, Any]:
        return SkillsAnalysisAgent().analyze(job)

    return Task(name="skills_analysis", coro=_run)


class CompensationAnalysisAgent:
    """Agent specialized in analyzing compensation and benefits."""
    
    def __init__(self, llm_router=None, web_search=None):
        """Initialize agent with optional LLM and web search capabilities."""
        self.llm_router = llm_router
        self.web_search = web_search
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compensation data."""
        if isinstance(job, dict):
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            description = job.get('description', '')
            title = job.get('title', '')
            company = job.get('company', '')
        else:
            salary_min = job.salary_min
            salary_max = job.salary_max
            description = job.description or ''
            title = job.title or ''
            company = job.company or ''
        
        # Basic salary analysis
        salary_analysis = self._analyze_salary_range(salary_min, salary_max)
        
        # Benefits extraction
        benefits = self._extract_benefits(description)
        
        # Enhanced analysis with LLM if available
        market_insights = {}
        if self.llm_router and title:
            try:
                market_insights = self._get_market_insights(title, company, salary_min, salary_max, description)
            except Exception as e:
                logger.warning(f"Failed to get market insights: {e}")
        
        result = {
            'salary_analysis': salary_analysis,
            'benefits_mentioned': benefits
        }
        
        if market_insights:
            result['market_insights'] = market_insights
            
        return result
    
    def _get_market_insights(self, title: str, company: str, salary_min, salary_max, description: str) -> Dict[str, Any]:
        """Get market insights using LLM and optional web search."""
        insights = {}
        
        # Use web search for market data if available
        if self.web_search and self.web_search.is_available():
            try:
                market_data = self.web_search.search_job_market(title, max_results=3)
                if market_data:
                    insights['market_data'] = [
                        f"{result['title']}: {result['content'][:100]}..."
                        for result in market_data[:2]
                    ]
            except Exception as e:
                logger.warning(f"Web search failed: {e}")
        
        # Use LLM to analyze compensation competitiveness
        if self.llm_router:
            salary_info = ""
            if salary_min and salary_max:
                salary_info = f"Salary range: ${salary_min:,} - ${salary_max:,}"
            elif salary_min:
                salary_info = f"Minimum salary: ${salary_min:,}"
            elif salary_max:
                salary_info = f"Maximum salary: ${salary_max:,}"
            else:
                salary_info = "Salary not specified"
            
            prompt = f"""
Analyze the compensation package for this job:

Job Title: {title}
Company: {company}
{salary_info}

Please provide:
1. Assessment of salary competitiveness (Below Market, Market Rate, Above Market, Premium)
2. Key benefits that should be negotiated if not mentioned
3. Overall compensation package rating (1-10)

Keep response concise (under 200 words).
"""
            
            response = self.llm_router.generate(prompt, max_tokens=300, temperature=0.3)
            insights['llm_analysis'] = response
        
        return insights
    
    def _analyze_salary_range(self, salary_min: Optional[float], salary_max: Optional[float]) -> Dict[str, Any]:
        """Analyze salary range and provide insights."""
        if not salary_min and not salary_max:
            return {
                'has_salary_info': False,
                'transparency_score': 0,
                'estimated_range': None,
                'competitiveness': 'Unknown'
            }
        
        avg_salary = None
        if salary_min and salary_max:
            avg_salary = (salary_min + salary_max) / 2
            transparency_score = 100
        elif salary_min:
            avg_salary = salary_min * 1.15  # Estimate 15% higher for max
            transparency_score = 70
        elif salary_max:
            avg_salary = salary_max * 0.87  # Estimate 13% lower for min
            transparency_score = 70
        
        # Basic competitiveness analysis (simplified)
        competitiveness = 'Average'
        if avg_salary:
            if avg_salary >= 150000:
                competitiveness = 'Highly Competitive'
            elif avg_salary >= 100000:
                competitiveness = 'Competitive'
            elif avg_salary >= 70000:
                competitiveness = 'Average'
            else:
                competitiveness = 'Below Average'
        
        return {
            'has_salary_info': True,
            'min_salary': salary_min,
            'max_salary': salary_max,
            'estimated_average': avg_salary,
            'transparency_score': transparency_score,
            'competitiveness': competitiveness
        }
    
    def _extract_benefits(self, description: str) -> List[str]:
        """Extract benefits mentioned in job description."""
        desc_lower = description.lower()
        
        benefit_patterns = {
            'health insurance': ['health', 'medical', 'dental', 'vision'],
            'retirement': ['401k', '401(k)', 'pension', 'retirement'],
            'paid time off': ['pto', 'paid time off', 'vacation', 'holidays'],
            'flexible work': ['flexible', 'remote', 'work from home', 'hybrid'],
            'professional development': ['training', 'learning', 'development', 'certification'],
            'stock options': ['equity', 'stock', 'options', 'rsu'],
            'bonus': ['bonus', 'incentive', 'commission'],
            'parental leave': ['maternity', 'paternity', 'parental leave'],
            'wellness': ['gym', 'fitness', 'wellness', 'mental health']
        }
        
        found_benefits = []
        for benefit, patterns in benefit_patterns.items():
            if any(pattern in desc_lower for pattern in patterns):
                found_benefits.append(benefit)

        return found_benefits


def build_compensation_task(job: Dict[str, Any]) -> "Task":
    """Create a task that runs the CompensationAnalysisAgent."""
    from .evaluation_pipeline import Task  # Local import to avoid circular dependency

    async def _run() -> Dict[str, Any]:
        analysis = CompensationAnalysisAgent().analyze(job)
        return {
            "salary_analysis": analysis["salary_analysis"],
            "benefits_mentioned": analysis["benefits_mentioned"],
        }

    return Task(name="compensation_analysis", coro=_run)


class QualityAssessmentAgent:
    """Agent specialized in assessing job posting quality and potential red flags."""
    
    def __init__(self, llm_router=None, web_search=None):
        """Initialize agent with optional LLM and web search capabilities."""
        self.llm_router = llm_router
        self.web_search = web_search
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess job posting quality."""
        description = job.get('description', '') if isinstance(job, dict) else (job.description or '')
        title = job.get('title', '') if isinstance(job, dict) else (job.title or '')
        company = job.get('company', '') if isinstance(job, dict) else (job.company or '')
        
        # Base quality analysis (rule-based)
        quality_score = self._calculate_quality_score(description, title, company)
        completeness = self._assess_completeness(description)
        red_flags = self._identify_red_flags(description, title)
        green_flags = self._identify_green_flags(description, title)
        
        result = {
            'job_quality_score': quality_score,
            'description_completeness': completeness,
            'red_flags': red_flags,
            'green_flags': green_flags
        }
        
        # Enhanced analysis with LLM if available
        if self.llm_router:
            try:
                llm_assessment = self._get_llm_quality_assessment(title, company, description)
                result['llm_quality_assessment'] = llm_assessment
                
                # Adjust quality score based on LLM insights
                if 'red flags' in llm_assessment.lower() or 'concerning' in llm_assessment.lower():
                    result['job_quality_score'] = max(0, quality_score - 10)
                elif 'excellent' in llm_assessment.lower() or 'high quality' in llm_assessment.lower():
                    result['job_quality_score'] = min(100, quality_score + 10)
                    
            except Exception as e:
                logger.warning(f"LLM quality assessment failed: {e}")
        
        # Get company insights if web search available
        if self.web_search and self.web_search.is_available() and company:
            try:
                company_info = self.web_search.search_company(company, max_results=2)
                if company_info:
                    result['company_insights'] = [
                        f"{info['title']}: {info['content'][:150]}..."
                        for info in company_info[:1]
                    ]
            except Exception as e:
                logger.warning(f"Company search failed: {e}")
        
        return result
    
    def _get_llm_quality_assessment(self, title: str, company: str, description: str) -> str:
        """Get LLM-based quality assessment."""
        prompt = f"""
Assess the quality of this job posting and identify any red or green flags:

Job Title: {title}
Company: {company}
Description: {description[:1000]}...

Please evaluate:
1. Clarity and completeness of job description
2. Realistic expectations and requirements
3. Any potential red flags (unrealistic demands, vague language, etc.)
4. Positive indicators (clear growth path, good benefits, etc.)
5. Overall professionalism of the posting

Provide a brief assessment (under 200 words) with an overall quality rating.
"""
        
        return self.llm_router.generate(prompt, max_tokens=300, temperature=0.3)
    
    def _calculate_quality_score(self, description: str, title: str, company: str) -> float:
        """Calculate overall job posting quality score."""
        score = 0.0
        
        # Basic information completeness (40 points)
        if title and len(title) > 5:
            score += 15
        if company and len(company) > 2:
            score += 10
        if description and len(description) > 100:
            score += 15
        
        # Description quality (40 points)
        if description:
            if len(description) > 500:
                score += 10
            if 'responsibilities' in description.lower() or 'duties' in description.lower():
                score += 10
            if 'requirements' in description.lower() or 'qualifications' in description.lower():
                score += 10
            if any(benefit in description.lower() for benefit in ['benefits', 'insurance', 'vacation']):
                score += 10
        
        # Professional presentation (20 points)
        if description and not any(flag in description.lower() for flag in ['urgent', '!!!', 'make money fast']):
            score += 10
        if title and title == title.title():  # Properly capitalized
            score += 10
        
        return min(score, 100.0)
    
    def _assess_completeness(self, description: str) -> float:
        """Assess how complete the job description is."""
        if not description:
            return 0.0
        
        completeness_indicators = [
            'responsibilities' in description.lower(),
            'requirements' in description.lower(),
            'qualifications' in description.lower(),
            'benefits' in description.lower(),
            'company' in description.lower(),
            len(description) > 300,
            len(description.split()) > 50
        ]
        
        return (sum(completeness_indicators) / len(completeness_indicators)) * 100
    
    def _identify_red_flags(self, description: str, title: str) -> List[str]:
        """Identify potential red flags in job posting."""
        desc_lower = description.lower()
        title_lower = title.lower()
        
        red_flags = []
        
        # Vague or misleading terms
        vague_terms = ['rockstar', 'ninja', 'guru', 'unicorn', 'make money fast', 'work from home (no experience)']
        if any(term in desc_lower or term in title_lower for term in vague_terms):
            red_flags.append('Uses vague or unprofessional terminology')
        
        # MLM or pyramid scheme indicators
        mlm_terms = ['unlimited earning potential', 'be your own boss', 'no experience necessary', 'make $5000/week']
        if any(term in desc_lower for term in mlm_terms):
            red_flags.append('Possible MLM or unrealistic income promises')
        
        # Poor grammar or excessive punctuation
        if '!!!' in description or description.count('!') > 5:
            red_flags.append('Excessive punctuation suggesting unprofessional posting')
        
        # Unrealistic requirements
        if 'entry level' in desc_lower and any(exp in desc_lower for exp in ['5+ years', '7+ years', '10+ years']):
            red_flags.append('Unrealistic experience requirements for entry-level position')
        
        return red_flags
    
    def _identify_green_flags(self, description: str, title: str) -> List[str]:
        """Identify positive indicators in job posting."""
        desc_lower = description.lower()
        
        green_flags = []
        
        # Professional indicators
        if any(term in desc_lower for term in ['professional development', 'career growth', 'mentorship']):
            green_flags.append('Emphasizes professional development')
        
        if any(term in desc_lower for term in ['work-life balance', 'flexible hours', 'remote options']):
            green_flags.append('Promotes work-life balance')
        
        if any(term in desc_lower for term in ['diverse', 'inclusive', 'equal opportunity']):
            green_flags.append('Emphasizes diversity and inclusion')
        
        if len(description) > 500:
            green_flags.append('Comprehensive job description')
        
        if any(term in desc_lower for term in ['health insurance', 'dental', 'vision', '401k', 'retirement']):
            green_flags.append('Mentions comprehensive benefits')

        return green_flags


def build_quality_task(job: Dict[str, Any]) -> "Task":
    """Create a task that runs the QualityAssessmentAgent."""
    from .evaluation_pipeline import Task  # Local import to avoid circular dependency

    async def _run() -> Dict[str, Any]:
        return QualityAssessmentAgent().analyze(job)

    return Task(name="quality_assessment", coro=_run)


class JobReviewCrew:
    """Crew configuration loading agents and tasks from YAML files."""
    _base_dir = Path(__file__).resolve().parent
    agents_config = str(_base_dir / "persona_catalog.yaml")
    tasks_config = str(_base_dir / "tasks.yaml")

    @crew
    def job_review(self) -> Crew:
        return Crew(
            agents=getattr(self, "agents", []),
            tasks=getattr(self, "tasks", []),
            process=Process.sequential,
        )



# Crew singleton
_job_review_crew: Optional[JobReviewCrew] = None


def get_job_review_crew() -> JobReviewCrew:
    """Get the singleton JobReviewCrew instance."""
    global _job_review_crew
    if _job_review_crew is None:
        _job_review_crew = JobReviewCrew()
    return _job_review_crew
