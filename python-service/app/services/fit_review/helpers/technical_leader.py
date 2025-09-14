"""
Technical Leader helper agent for job posting fit review.

This module implements the technical leader persona that evaluates jobs
from an engineering leadership and technical excellence perspective.
"""
from typing import Dict, Any
from loguru import logger

from ....models.job_posting import JobPosting
from ....models.fit_review import PersonaVerdict


class TechnicalLeaderHelper:
    """Technical leader persona for evaluating job postings."""
    
    def __init__(self):
        """Initialize the technical leader helper."""
        self.persona_id = "technical_leader"
        logger.info("TechnicalLeaderHelper initialized")
    
    async def evaluate(
        self, 
        job_posting: JobPosting, 
        context: Dict[str, Any]
    ) -> PersonaVerdict:
        """
        Evaluate job posting from technical leader perspective.
        
        Args:
            job_posting: Job posting to evaluate
            context: Additional context and normalized job data
            
        Returns:
            Persona verdict with recommendation
        """
        logger.debug(f"Technical leader evaluating: {job_posting.title}")
        
        # TODO: Implement technical leader evaluation logic
        # Focus areas:
        # - Technical challenges and complexity
        # - Engineering practices and culture
        # - Technology stack modernity and sustainability
        # - Team leadership and mentorship opportunities
        
        # Placeholder evaluation
        tech_leadership_terms = ["technical lead", "architecture", "engineering", "mentorship", "code review", "best practices"]
        modern_tech_terms = ["cloud", "microservices", "kubernetes", "ci/cd", "devops", "agile"]
        
        description_lower = job_posting.description.lower()
        
        leadership_score = sum(1 for term in tech_leadership_terms if term in description_lower)
        tech_score = sum(1 for term in modern_tech_terms if term in description_lower)
        
        total_score = leadership_score + tech_score
        recommend = total_score >= 4  # Arbitrary threshold for demo
        
        reason = f"Technical leadership score: {total_score}/12 (leadership: {leadership_score}, tech: {tech_score})"
        notes = [
            f"Leadership aspects: {leadership_score}/6",
            f"Modern tech stack: {tech_score}/6",
            "Placeholder analysis - full implementation pending"
        ]
        
        verdict = PersonaVerdict(
            id=self.persona_id,
            recommend=recommend,
            reason=reason,
            notes=notes,
            sources=["job_description", "tech_stack_analysis"]
        )
        
        logger.debug(f"Technical leader verdict: {recommend}")
        return verdict