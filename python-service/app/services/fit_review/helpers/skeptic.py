"""
Skeptic helper agent for job posting fit review.

This module implements the skeptic persona that evaluates jobs
with critical analysis and identifies potential risks and concerns.
"""
from typing import Dict, Any
from loguru import logger

from ....models.job_posting import JobPosting
from ....models.fit_review import PersonaVerdict


class SkepticHelper:
    """Skeptic persona for evaluating job postings."""
    
    def __init__(self):
        """Initialize the skeptic helper."""
        self.persona_id = "skeptic"
        logger.info("SkepticHelper initialized")
    
    async def evaluate(
        self, 
        job_posting: JobPosting, 
        context: Dict[str, Any]
    ) -> PersonaVerdict:
        """
        Evaluate job posting from skeptic perspective.
        
        Args:
            job_posting: Job posting to evaluate
            context: Additional context and normalized job data
            
        Returns:
            Persona verdict with recommendation
        """
        logger.debug(f"Skeptic evaluating: {job_posting.title}")
        
        # TODO: Implement skeptic evaluation logic
        # Focus areas:
        # - Red flags and warning signs
        # - Unrealistic expectations or requirements
        # - Vague job descriptions or responsibilities
        # - Company stability and reputation concerns
        
        # Placeholder evaluation
        warning_signs = [
            "urgent", "asap", "hit the ground running", "startup mentality",
            "unlimited pto", "we work hard play hard", "fast-paced environment",
            "rockstar", "ninja", "guru", "10x developer"
        ]
        
        vague_terms = [
            "other duties as assigned", "various tasks", "ad hoc", 
            "flexible role", "wearing many hats", "dynamic environment"
        ]
        
        description_lower = job_posting.description.lower()
        
        warning_score = sum(1 for warning in warning_signs if warning in description_lower)
        vague_score = sum(1 for term in vague_terms if term in description_lower)
        
        total_concerns = warning_score + vague_score
        
        # Skeptic recommends only when concerns are minimal
        recommend = total_concerns <= 2
        
        reason = f"Risk assessment: {total_concerns} concerns identified (warnings: {warning_score}, vague terms: {vague_score})"
        notes = [
            f"Warning signs detected: {warning_score}",
            f"Vague descriptions: {vague_score}",
            "Consider investigating company culture and expectations",
            "Placeholder analysis - full implementation pending"
        ]
        
        verdict = PersonaVerdict(
            id=self.persona_id,
            recommend=recommend,
            reason=reason,
            notes=notes,
            sources=["job_description", "company_reviews"]
        )
        
        logger.debug(f"Skeptic verdict: {recommend} (concerns: {total_concerns})")
        return verdict