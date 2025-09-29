"""Natural Language Feedback Transformer for Career Brand Analysis."""

from typing import Dict, Any, List
from loguru import logger


class FeedbackTransformer:
    """Transforms technical agent scoring outputs into human-readable explanations."""

    def __init__(self):
        self.score_ranges = {
            "north_star": {
                1: "Fundamentally misaligned with your long-term career vision and aspirations",
                2: "Some concerns about long-term career direction and strategic fit",
                3: "Generally aligned with your career direction but room for improvement",
                4: "Strong alignment with your career vision and professional goals",
                5: "Exceptional fit with your career aspirations and long-term objectives"
            },
            "trajectory_mastery": {
                1: "Prevents development of required skills and represents career regression",
                2: "Limited learning opportunities that may stall skill development",
                3: "Some skill utilization but minimal opportunities to grow expertise",
                4: "Good balance of current skill application and future development potential",
                5: "Perfect match for accelerating your skills and reaching mastery goals"
            },
            "values_compass": {
                1: "Significant conflict with your core values and work style preferences",
                2: "Some value differences that could impact daily work satisfaction",
                3: "Generally compatible values with manageable style differences",
                4: "Strong alignment with your values and positive work environment signals",
                5: "Exceptional cultural fit with inspiring alignment on work style and principles"
            },
            "lifestyle_alignment": {
                1: "Incompatible with your family commitments and geographical requirements",
                2: "Some concerns about work-life balance and location flexibility",
                3: "Manageable arrangement with acceptable trade-offs for family/life balance",
                4: "Good support for your lifestyle with positive work-life balance signals",
                5: "Perfect match for your family commitments and preferred work arrangement"
            },
            "compensation_philosophy": {
                1: "Significantly below your salary floor with unacceptable equity/terms",
                2: "Below your target range and may not meet growth compensation needs",
                3: "Meets your floor but below target range or preferred structure",
                4: "Solid compensation with good alignment to your financial expectations",
                5: "Exceptional package matching your financial goals and growth expectations"
            },
            "purpose_impact": {
                1: "Does not support making the world better through societal contribution",
                2: "Moderate societal impact potential but not core mission-focused",
                3: "Some opportunity for positive impact but not central to the role",
                4: "Meaningful opportunity to create positive societal impact",
                5: "Exceptional opportunity to create major positive impact on the world"
            },
            "industry_focus": {
                1: "Not in your preferred sectors (Healthcare, EdTech, Productivity, FinTech)",
                2: "Outside your most preferred domains but somewhat adjacent",
                3: "Neutral industry position that doesn't conflict with your preferences",
                4: "Good alignment with some of your preferred sectors and domains",
                5: "Perfect fit within your top-priority industries and sectors"
            },
            "company_filters": {
                1: "Matches organizations you avoid (PE-backed, IT security, extractive industries)",
                2: "Some concerning organizational signals that may not align with your preferences",
                3: "Neutral organization structure without strong positive or negative signals",
                4: "Good alignment with your preferred company types and cultures",
                5: "Exceptional match with your ideal organizational structure and mission focus"
            },
            "constraints": {
                1: "Violates deal-breakers (toxic culture, founder micromanagement, geography blocks)",
                2: "Multiple constraint concerns that significantly impact viability",
                3: "One minor constraint issue but largely compliant with your requirements",
                4: "Fully compliant and demonstrates positive signals in key areas",
                5: "Perfect compliance with immediate availability and ideal timing factors"
            }
        }

    async def transform_feedback(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform technical scoring into human-readable explanations.

        Input: Raw agent analysis with numerical scores
        Output: Same structure but with readable explanations instead of just scores
        """
        try:
            transformed = analysis_results.copy()

            # Transform individual dimension assessments
            dimensions = [
                "north_star", "trajectory_mastery", "values_compass", "lifestyle_alignment",
                "compensation_philosophy", "purpose_impact", "industry_focus", "company_filters", "constraints"
            ]

            for dimension in dimensions:
                if dimension in transformed and "score" in transformed[dimension]:
                    raw_score = transformed[dimension]["score"]
                    if isinstance(raw_score, int) and 1 <= raw_score <= 5:
                        readable_explanation = self.score_ranges[dimension].get(
                            raw_score,
                            f"Unexpected score {raw_score} for {dimension}"
                        )

                        # Replace or enhance the summary field
                        original_summary = transformed[dimension].get("summary", "")
                        if original_summary:
                            # Leverage existing specific details with readable explanation
                            transformed[dimension]["readable_explanation"] = f"{readable_explanation}: {original_summary}"
                        else:
                            transformed[dimension]["readable_explanation"] = readable_explanation

            # Transform overall summary to be more actionable
            # Convert overall score to meaningful recommendation tier
            overall_score = transformed.get("overall_alignment_score", 0)
            if "overall_summary" in transformed:
                transformed["overall_summary"] = self._enhance_overall_summary(
                    overall_score, transformed["overall_summary"]
                )

            # Add constraint issues in readable format
            if "constraint_issues" in transformed:
                transformed["readable_constraint_issues"] = self._make_constraint_issues_readable(
                    transformed["constraint_issues"]
                )

            logger.info("Successfully transformed agent feedback into natural language explanations")
            return transformed

        except Exception as e:
            logger.error(f"Failed to transform feedback: {e}")
            # Return original results if transformation fails
            return analysis_results

    def _enhance_overall_summary(self, overall_score: float, original_summary: str) -> str:
        """Enhance the overall summary with actionable language."""
        score_tier = self._get_score_tier(overall_score)

        if "Not recommend" in original_summary or "DO NOT" in original_summary:
            enhanced = f"{score_tier} - Additional research recommended before applying. {original_summary}"
        elif "recommend" in original_summary.lower():
            enhanced = f"{score_tier} - Consider applying with {original_summary.lower()}"
        else:
            enhanced = f"{score_tier}. {original_summary}"

        return enhanced

    def _get_score_tier(self, score: float) -> str:
        """Convert numerical score to meaningful tier description."""
        if score >= 8.5:
            return "⭐ Exceptional Match"
        elif score >= 8.25:
            return "✅ Strong Recommendation"
        elif score >= 7.9:
            return "👍 Good Opportunity"
        elif score >= 7.6:
            return "🤔 Borderline - Consider Carefully"
        elif score >= 7.0:
            return "⚠️ Potential Concerns - Research More"
        else:
            return "❌ Not Recommended"

    def _make_constraint_issues_readable(self, constraint_issues: str) -> str:
        """Convert technical constraint issues into user-friendly language."""
        if constraint_issues.lower() == "none":
            return "No constraint violations detected"

        # Map common technical constraint language to user-friendly explanations
        readable_map = {
            "toxic culture": "Potential toxic work environment indicators",
            "founder micromanagement": "History of founder control issues that may limit autonomy",
            "geography": "Location requirements not matching your preferred geography",
            "citizenship": "Citizenship or work authorization requirements that may not apply to you",
            "immediate availability": "Requires immediate start which may conflict with your timeline"
        }

        readable_parts = []
        for issue in constraint_issues.split(","):
            issue = issue.strip().lower()
            for tech_term, readable in readable_map.items():
                if tech_term in issue:
                    readable_parts.append(readable)
                    break
            else:
                # If no mapping found, use the original but make it more readable
                readable_parts.append(issue.replace("_", " ").title())

        return " • ".join(readable_parts)

    def get_dimension_explanation(self, dimension: str, score: int) -> str:
        """Get readable explanation for a specific dimension and score."""
        if dimension in self.score_ranges and isinstance(score, int) and 1 <= score <= 5:
            return self.score_ranges[dimension][score]
        return f"Unexpected score {score} for {dimension}"


# Global transformer instance
_feedback_transformer = None


def get_feedback_transformer() -> FeedbackTransformer:
    """Get the global feedback transformer instance."""
    global _feedback_transformer
    if _feedback_transformer is None:
        _feedback_transformer = FeedbackTransformer()
    return _feedback_transformer
