"""
Judge component for aggregating persona verdicts into final decisions.

This module implements deterministic aggregation logic to combine
individual persona verdicts into a final recommendation.
"""
from typing import List, Dict, Any
from loguru import logger

from ...models.fit_review import PersonaVerdict, JudgeDecision, ConfidenceLevel


class FitReviewJudge:
    """Judge that aggregates persona verdicts into final decisions."""
    
    def __init__(self):
        """Initialize the judge component."""
        logger.info("FitReviewJudge initialized")
    
    def decide(
        self,
        verdicts: List[PersonaVerdict],
        weights: Dict[str, float],
        guardrails: Dict[str, Any],
        job_meta: Dict[str, Any]
    ) -> JudgeDecision:
        """
        Make final decision based on persona verdicts and configuration.
        
        Args:
            verdicts: List of persona verdicts
            weights: Weights for different persona types
            guardrails: Guardrail configuration
            job_meta: Additional job metadata
            
        Returns:
            Final judge decision
        """
        logger.info(f"Judge processing {len(verdicts)} verdicts")
        
        # TODO: Implement deterministic aggregation logic
        # 1. Apply weights to persona verdicts
        # 2. Check guardrails (comp_floor_enforced, severe_redflags_block)
        # 3. Handle tie_bias according to configuration
        # 4. Calculate confidence based on consensus
        
        # Placeholder implementation
        positive_votes = sum(1 for v in verdicts if v.recommend)
        total_votes = len(verdicts)
        
        # Simple majority rule for now
        final_recommendation = positive_votes > total_votes / 2
        
        # Apply tie bias if configured
        tie_bias = guardrails.get("tie_bias", "do_not_pursue")
        if positive_votes == total_votes / 2:
            final_recommendation = tie_bias != "do_not_pursue"
        
        # Calculate confidence based on consensus strength
        consensus_ratio = max(positive_votes, total_votes - positive_votes) / total_votes
        if consensus_ratio >= 0.8:
            confidence = ConfidenceLevel.HIGH
        elif consensus_ratio >= 0.6:
            confidence = ConfidenceLevel.MEDIUM
        else:
            confidence = ConfidenceLevel.LOW
        
        # Collect key tradeoffs mentioned by personas
        tradeoffs = []
        for verdict in verdicts:
            if verdict.notes:
                tradeoffs.extend([note for note in verdict.notes if "vs" in note.lower() or "tradeoff" in note.lower()])
        
        decision = JudgeDecision(
            final_recommendation=final_recommendation,
            primary_rationale=f"Verdict based on {positive_votes}/{total_votes} positive recommendations",
            tradeoffs=tradeoffs[:5],  # Limit to top 5 tradeoffs
            decider_confidence=confidence
        )
        
        logger.info(f"Judge decision: {final_recommendation} with {confidence} confidence")
        return decision