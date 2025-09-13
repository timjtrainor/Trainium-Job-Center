"""
Data Analyst helper agent for job posting fit review.

This module implements the data analyst persona that evaluates jobs
from a data-driven perspective, focusing on metrics and analytics.
"""
from typing import Dict, Any
from loguru import logger

from ....models.job_posting import JobPosting
from ....models.fit_review import PersonaVerdict


class DataAnalystHelper:
    """Data analyst persona for evaluating job postings."""
    
    def __init__(self):
        """Initialize the data analyst helper."""
        self.persona_id = "data_analyst"
        logger.info("DataAnalystHelper initialized")
    
    async def evaluate(
        self, 
        job_posting: JobPosting, 
        context: Dict[str, Any]
    ) -> PersonaVerdict:
        """
        Evaluate job posting from data analyst perspective.
        
        Args:
            job_posting: Job posting to evaluate
            context: Additional context and normalized job data
            
        Returns:
            Persona verdict with recommendation
        """
        logger.debug(f"Data analyst evaluating: {job_posting.title}")
        
        # TODO: Implement data analyst evaluation logic
        # Focus areas:
        # - Data infrastructure and tools mentioned
        # - Analytics responsibilities and growth potential
        # - Team size and data maturity indicators
        # - Quantitative aspects of the role
        
        # Placeholder evaluation
        data_terms = ["data", "analytics", "sql", "python", "tableau", "powerbi", "warehouse"]
        description_lower = job_posting.description.lower()
        
        data_score = sum(1 for term in data_terms if term in description_lower)
        recommend = data_score >= 3  # Arbitrary threshold for demo
        
        reason = f"Data focus score: {data_score}/7 based on key terms"
        notes = [
            f"Found {data_score} data-related terms",
            "Placeholder analysis - full implementation pending"
        ]
        
        verdict = PersonaVerdict(
            id=self.persona_id,
            recommend=recommend,
            reason=reason,
            notes=notes,
            sources=["job_description"]
        )
        
        logger.debug(f"Data analyst verdict: {recommend}")
        return verdict