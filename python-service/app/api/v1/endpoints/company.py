from fastapi import APIRouter, HTTPException
from ....schemas.company import CompanyRequest, CompanyReportResponse
from ....services.company_service import generate_company_report

router = APIRouter(prefix="/company", tags=["Company Research"])

@router.post("/report", response_model=CompanyReportResponse)
async def company_report(request: CompanyRequest):
    try:
        report = generate_company_report(request.company_name)
        return CompanyReportResponse(report=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))