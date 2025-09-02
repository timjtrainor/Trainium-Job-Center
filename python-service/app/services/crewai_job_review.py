"""
CrewAI-inspired job review service for multi-agent job analysis.

This service implements a multi-agent approach to job review, where different
specialized "agents" analyze various aspects of job postings to provide
comprehensive insights and recommendations.
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import json
import re
from loguru import logger
from dataclasses import dataclass, asdict

from ..core.config import get_settings
from ..models.jobspy import ScrapedJob
from .database import get_database_service
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - used for type hints only
    from .evaluation_pipeline import Task


@dataclass
class JobAnalysis:
    """Result of job analysis by various agents."""
    job_id: str
    title: str
    company: str
    
    # Skills and Requirements Analysis
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str
    education_requirements: str
    
    # Compensation Analysis
    salary_analysis: Dict[str, Any]
    benefits_mentioned: List[str]
    
    # Quality and Fit Analysis
    job_quality_score: float  # 0-100
    description_completeness: float  # 0-100
    red_flags: List[str]
    green_flags: List[str]
    
    # Market and Company Analysis
    company_insights: Dict[str, Any]
    industry_category: str
    remote_work_options: str
    
    # Overall Assessment
    overall_recommendation: str
    confidence_score: float  # 0-100
    
    # Metadata
    analysis_timestamp: datetime
    agents_used: List[str]


class SkillsAnalysisAgent:
    """Agent specialized in analyzing job skills and requirements."""
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze skills and requirements from job description."""
        description = job.get('description', '') if isinstance(job, dict) else (job.description or '')
        title = job.get('title', '') if isinstance(job, dict) else (job.title or '')
        
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
            elif any(pref in desc_lower for req in [f'preferred {skill_lower}', f'{skill_lower} preferred', 'nice to have', 'bonus']):
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
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze compensation data."""
        if isinstance(job, dict):
            salary_min = job.get('salary_min')
            salary_max = job.get('salary_max')
            description = job.get('description', '')
        else:
            salary_min = job.salary_min
            salary_max = job.salary_max
            description = job.description or ''
        
        # Salary analysis
        salary_analysis = self._analyze_salary_range(salary_min, salary_max)
        
        # Benefits extraction
        benefits = self._extract_benefits(description)
        
        return {
            'salary_analysis': salary_analysis,
            'benefits_mentioned': benefits
        }
    
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
    
    def analyze(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Assess job posting quality."""
        description = job.get('description', '') if isinstance(job, dict) else (job.description or '')
        title = job.get('title', '') if isinstance(job, dict) else (job.title or '')
        company = job.get('company', '') if isinstance(job, dict) else (job.company or '')
        
        # Quality score based on completeness
        quality_score = self._calculate_quality_score(description, title, company)
        
        # Description completeness
        completeness = self._assess_completeness(description)
        
        # Red and green flags
        red_flags = self._identify_red_flags(description, title)
        green_flags = self._identify_green_flags(description, title)
        
        return {
            'job_quality_score': quality_score,
            'description_completeness': completeness,
            'red_flags': red_flags,
            'green_flags': green_flags
        }
    
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


class CrewAIJobReviewService:
    """Main service orchestrating multiple agents for comprehensive job review."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_service = get_database_service()
        self.skills_agent = SkillsAnalysisAgent()
        self.compensation_agent = CompensationAnalysisAgent()
        self.quality_agent = QualityAssessmentAgent()
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the job review service."""
        try:
            if not self.db_service.initialized:
                await self.db_service.initialize()
            
            self.initialized = True
            logger.info("CrewAI Job Review Service initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI Job Review Service: {str(e)}")
            return False
    
    async def analyze_job(self, job: Union[ScrapedJob, Dict[str, Any]], job_id: Optional[str] = None) -> JobAnalysis:
        """
        Perform comprehensive job analysis using multiple agents.
        
        Args:
            job: ScrapedJob object or dictionary with job data
            job_id: Optional job identifier
            
        Returns:
            JobAnalysis object with comprehensive analysis results
        """
        if not self.initialized:
            await self.initialize()
        
        logger.info(f"Starting comprehensive job analysis for job: {job_id}")
        
        # Extract basic job info
        if isinstance(job, dict):
            title = job.get('title', 'Unknown')
            company = job.get('company', 'Unknown')
        else:
            title = job.title or 'Unknown'
            company = job.company or 'Unknown'
        
        # Run agents in parallel conceptually (for now, sequentially)
        skills_analysis = self.skills_agent.analyze(job)
        compensation_analysis = self.compensation_agent.analyze(job)
        quality_analysis = self.quality_agent.analyze(job)
        
        # Company and market analysis (simplified)
        company_insights = self._analyze_company_and_market(job)
        
        # Calculate overall recommendation
        overall_recommendation, confidence_score = self._calculate_overall_assessment(
            skills_analysis, compensation_analysis, quality_analysis
        )
        
        # Create analysis result
        analysis = JobAnalysis(
            job_id=job_id or f"job_{datetime.now().timestamp()}",
            title=title,
            company=company,
            required_skills=skills_analysis['required_skills'],
            preferred_skills=skills_analysis['preferred_skills'],
            experience_level=skills_analysis['experience_level'],
            education_requirements=skills_analysis['education_requirements'],
            salary_analysis=compensation_analysis['salary_analysis'],
            benefits_mentioned=compensation_analysis['benefits_mentioned'],
            job_quality_score=quality_analysis['job_quality_score'],
            description_completeness=quality_analysis['description_completeness'],
            red_flags=quality_analysis['red_flags'],
            green_flags=quality_analysis['green_flags'],
            company_insights=company_insights,
            industry_category=company_insights.get('industry', 'Unknown'),
            remote_work_options=company_insights.get('remote_options', 'Not specified'),
            overall_recommendation=overall_recommendation,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.now(timezone.utc),
            agents_used=['SkillsAnalysisAgent', 'CompensationAnalysisAgent', 'QualityAssessmentAgent']
        )
        
        logger.info(f"Job analysis completed for {job_id}: {overall_recommendation} (confidence: {confidence_score:.1f}%)")
        return analysis
    
    def _analyze_company_and_market(self, job: Union[ScrapedJob, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze company and market context (simplified implementation)."""
        description = job.get('description', '') if isinstance(job, dict) else (job.description or '')
        location = job.get('location', '') if isinstance(job, dict) else (job.location or '')
        is_remote = job.get('is_remote', False) if isinstance(job, dict) else (job.is_remote or False)
        
        # Simple industry categorization
        industry = self._categorize_industry(description)
        
        # Remote work analysis
        remote_options = 'Full Remote' if is_remote else self._analyze_remote_options(description)
        
        return {
            'industry': industry,
            'remote_options': remote_options,
            'location': location
        }
    
    def _categorize_industry(self, description: str) -> str:
        """Simple industry categorization based on job description."""
        desc_lower = description.lower()
        
        industry_keywords = {
            'Technology': ['software', 'tech', 'developer', 'engineer', 'programming', 'coding'],
            'Finance': ['finance', 'banking', 'investment', 'fintech', 'trading'],
            'Healthcare': ['healthcare', 'medical', 'hospital', 'health', 'pharmaceutical'],
            'Education': ['education', 'teaching', 'school', 'university', 'learning'],
            'Marketing': ['marketing', 'advertising', 'brand', 'campaign', 'digital marketing'],
            'Sales': ['sales', 'business development', 'account manager', 'revenue'],
            'Consulting': ['consulting', 'consultant', 'advisory', 'strategy']
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return industry
        
        return 'Other'
    
    def _analyze_remote_options(self, description: str) -> str:
        """Analyze remote work options from description."""
        desc_lower = description.lower()
        
        if 'full remote' in desc_lower or 'fully remote' in desc_lower:
            return 'Full Remote'
        elif 'hybrid' in desc_lower or 'remote option' in desc_lower:
            return 'Hybrid/Optional Remote'
        elif 'on-site' in desc_lower or 'office' in desc_lower:
            return 'On-site'
        else:
            return 'Not specified'
    
    def _calculate_overall_assessment(self, skills_analysis: Dict, compensation_analysis: Dict, quality_analysis: Dict) -> tuple:
        """Calculate overall recommendation and confidence score."""
        # Weight different factors
        quality_score = quality_analysis['job_quality_score']
        completeness_score = quality_analysis['description_completeness']
        has_salary = compensation_analysis['salary_analysis'].get('has_salary_info', False)
        red_flags_count = len(quality_analysis['red_flags'])
        green_flags_count = len(quality_analysis['green_flags'])
        
        # Calculate weighted score
        weighted_score = (
            quality_score * 0.4 +
            completeness_score * 0.3 +
            (20 if has_salary else 0) * 0.1 +
            max(0, (green_flags_count - red_flags_count)) * 5 * 0.2
        )
        
        # Determine recommendation
        if weighted_score >= 80 and red_flags_count == 0:
            recommendation = 'Highly Recommended'
        elif weighted_score >= 65 and red_flags_count <= 1:
            recommendation = 'Recommended'
        elif weighted_score >= 45:
            recommendation = 'Consider with Caution'
        else:
            recommendation = 'Not Recommended'
        
        # Confidence based on data quality
        confidence = min(95, max(20, weighted_score * 0.8 + (completeness_score * 0.2)))
        
        return recommendation, confidence
    
    async def analyze_multiple_jobs(self, jobs: List[Union[ScrapedJob, Dict[str, Any]]]) -> List[JobAnalysis]:
        """Analyze multiple jobs and return sorted results."""
        analyses = []
        
        for i, job in enumerate(jobs):
            try:
                job_id = f"batch_job_{i}"
                analysis = await self.analyze_job(job, job_id)
                analyses.append(analysis)
            except Exception as e:
                logger.error(f"Failed to analyze job {i}: {str(e)}")
        
        # Sort by overall recommendation quality
        recommendation_order = {
            'Highly Recommended': 4,
            'Recommended': 3,
            'Consider with Caution': 2,
            'Not Recommended': 1
        }
        
        analyses.sort(
            key=lambda x: (recommendation_order.get(x.overall_recommendation, 0), x.confidence_score),
            reverse=True
        )
        
        return analyses
    
    def analysis_to_dict(self, analysis: JobAnalysis) -> Dict[str, Any]:
        """Convert JobAnalysis to dictionary for API responses."""
        return asdict(analysis)


# Service singleton
_job_review_service = None


def get_crewai_job_review_service() -> CrewAIJobReviewService:
    """Get the singleton CrewAI job review service instance."""
    global _job_review_service
    if _job_review_service is None:
        _job_review_service = CrewAIJobReviewService()
    return _job_review_service
