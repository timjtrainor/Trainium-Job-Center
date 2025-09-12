from pydantic import BaseModel


class CompanyRequest(BaseModel):
    company_name: str


class CompanyReport(BaseModel):
    recent_news: list[str]


class CompanyReportResponse(BaseModel):
    report: CompanyReport
