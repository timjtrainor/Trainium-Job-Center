from typing import Optional
from pydantic import BaseModel, Field

class JobParseRequest(BaseModel):
    description: str = Field(..., description="Raw job description text")
    url: Optional[str] = Field(None, description="Job posting URL")

class JobParseResponse(BaseModel):
    title: Optional[str] = Field(None, description="Job title")
    company_name: Optional[str] = Field(None, description="Company name")
    description: Optional[str] = Field(None, description="Cleaned or formatted job description")
    location: Optional[str] = Field(None, description="Job location")
    salary_min: Optional[float] = Field(None, description="Minimum salary")
    salary_max: Optional[float] = Field(None, description="Maximum salary")
    salary_currency: str = Field("USD", description="Salary currency")
    remote_status: Optional[str] = Field(None, description="Remote work status (Remote, Hybrid, On-site)")
    date_posted: Optional[str] = Field(None, description="Date posted in YYYY-MM-DD format")
