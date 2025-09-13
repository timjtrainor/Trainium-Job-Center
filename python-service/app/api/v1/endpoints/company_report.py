"""Endpoints for company report generation."""
from fastapi import APIRouter

from ....schemas.responses import StandardResponse, create_success_response
from ....services.company_report import get_company_report

router = APIRouter()


@router.get("/companies/{company_name}/report", response_model=StandardResponse)
async def fetch_company_report(company_name: str) -> StandardResponse:
    """Return a company report for the given company name."""
    report = await get_company_report(company_name)
    return create_success_response(data=report)
