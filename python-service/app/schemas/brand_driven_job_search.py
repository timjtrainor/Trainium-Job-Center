"""
Schemas for Brand-Driven Job Search CrewAI integration.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from .jobspy import ScrapedJob


class BrandJobMetadata(BaseModel):
    """Metadata for brand-driven job results."""
    originating_section: str = Field(description="Brand section that led to job discovery")
    search_keywords: str = Field(description="Keywords used in the search")
    overall_brand_score: int = Field(ge=0, le=100, description="Overall brand alignment score")
    priority: str = Field(description="Job priority level (high/medium/low)")
    brand_alignments: Dict[str, int] = Field(description="Scores for each brand dimension")


class BrandDrivenJob(ScrapedJob):
    """Extended ScrapedJob with brand alignment metadata."""
    brand_metadata: Optional[BrandJobMetadata] = Field(default=None, description="Brand alignment metadata")


class BrandDrivenJobSearchRequest(BaseModel):
    """Request model for brand-driven job search."""
    user_id: str = Field(..., description="User ID for personalized brand data retrieval")
    limit_per_section: int = Field(default=10, ge=1, le=50, description="Maximum jobs per brand section")


class ExecutionSummary(BaseModel):
    """Summary of brand-driven search execution."""
    total_jobs_found: int = Field(description="Total number of jobs discovered")
    brand_sections_queried: int = Field(description="Number of brand sections successfully queried")
    successful_searches: int = Field(description="Number of successful LinkedIn searches")
    high_priority_jobs: int = Field(description="Number of high-priority job matches")
    autonomous_search_success: bool = Field(description="Whether the autonomous search succeeded overall")


class BrandInsights(BaseModel):
    """Insights about brand section effectiveness."""
    most_productive_section: str = Field(description="Brand section that found the most relevant jobs")
    best_aligned_opportunities: int = Field(description="Number of highly aligned opportunities")
    search_effectiveness: Dict[str, Dict[str, Any]] = Field(
        description="Effectiveness metrics for each brand section"
    )


class BrandDrivenJobSearchResponse(BaseModel):
    """Response model for brand-driven job search results."""
    success: bool = Field(description="Whether the search was successful")
    brand_driven_jobs: List[BrandDrivenJob] = Field(description="List of brand-aligned job results")
    execution_summary: ExecutionSummary = Field(description="Search execution summary")
    brand_insights: Optional[BrandInsights] = Field(default=None, description="Brand effectiveness insights")
    user_id: str = Field(description="User ID for the search")
    error: Optional[str] = Field(default=None, description="Error message if search failed")


class BrandSearchStatus(BaseModel):
    """Status model for brand data availability."""
    user_id: str = Field(description="User ID")
    brand_data_available: bool = Field(description="Whether brand data is available for the user")
    brand_sections: List[str] = Field(description="Available brand sections")
    can_execute_search: bool = Field(description="Whether brand-driven search can be executed")
    error: Optional[str] = Field(default=None, description="Error message if status check failed")


class BrandQuery(BaseModel):
    """Model for brand-derived search queries."""
    keywords: str = Field(description="Search keywords")
    search_terms: List[str] = Field(description="Individual search terms")
    job_types: List[str] = Field(description="Job type filters")
    brand_section: str = Field(description="Originating brand section")
    section_content: str = Field(description="Brief excerpt from brand content")
    total_keywords: int = Field(description="Total number of keywords extracted")


class BrandQueriesResponse(BaseModel):
    """Response model for brand query generation."""
    success: bool = Field(description="Whether query generation was successful")
    brand_queries: Dict[str, BrandQuery] = Field(description="Generated queries by brand section")
    total_queries: int = Field(description="Total number of queries generated")
    user_id: str = Field(description="User ID")
    error: Optional[str] = Field(default=None, description="Error message if generation failed")