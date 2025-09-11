from pydantic import BaseModel

class CompanyRequest(BaseModel):
    company_name: str

class CompanyReportResponse(BaseModel):
    report: dict  # since your writer returns JSON