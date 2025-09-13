"""
Recruiter helper agent for job posting fit review.

This module implements the recruiter persona that evaluates jobs
from a hiring and candidate fit perspective.
"""
from typing import Dict, Any
from loguru import logger

from ....models.job_posting import JobPosting
from ....models.fit_review import PersonaVerdict


class RecruiterHelper:
    """Recruiter persona for evaluating job postings."""
    
    def __init__(self):
        """Initialize the recruiter helper."""
        self.persona_id = "recruiter"
        logger.info("RecruiterHelper initialized")
    
    async def evaluate(
        self, 
        job_posting: JobPosting, 
        context: Dict[str, Any]
    ) -> PersonaVerdict:
        """
        Evaluate job posting from recruiter perspective.
        
        Args:
            job_posting: Job posting to evaluate
            context: Additional context and normalized job data
            
        Returns:
            Persona verdict with recommendation
        """
        logger.debug(f"Recruiter evaluating: {job_posting.title}")
        
        # TODO: Implement recruiter evaluation logic
        # Focus areas:
        # - Job posting quality and clarity
        # - Realistic requirements vs. expectations
        # - Compensation competitiveness
        # - Company attractiveness to candidates
        
        # Placeholder evaluation
        positive_signals = ["competitive salary", "benefits", "growth", "remote", "flexible", "training"]
        red_flags = ["rockstar", "ninja", "guru", "unlimited pto", "fast-paced", "wearing many hats"]
        
        description_lower = job_posting.description.lower()
        
        positive_score = sum(1 for signal in positive_signals if signal in description_lower)
        red_flag_score = sum(1 for flag in red_flags if flag in description_lower)
        
        # Calculate net attractiveness score
        net_score = positive_score - red_flag_score
        recommend = net_score >= 1  # Must have more positives than red flags
        
        reason = f"Candidate attractiveness score: {net_score} (positives: {positive_score}, red flags: {red_flag_score})"
        notes = [
            f"Found {positive_score} positive signals",
            f"Found {red_flag_score} potential red flags",
            "Placeholder analysis - full implementation pending"
        ]
        
        verdict = PersonaVerdict(
            id=self.persona_id,
            recommend=recommend,
            reason=reason,
            notes=notes,
            sources=["job_description", "market_standards"]
        )
        
        logger.debug(f"Recruiter verdict: {recommend}")
        return verdict