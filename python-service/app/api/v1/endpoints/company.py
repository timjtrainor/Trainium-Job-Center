from fastapi import APIRouter, HTTPException
from ....schemas.company import CompanyRequest, CompanyReportResponse, CompanyWebResearchResult
from ....services.company_service import generate_company_report
from ....services.ai.ai_service import ai_service
import logging
import asyncio
from functools import partial

router = APIRouter(prefix="/company", tags=["Company Research"])

@router.post("/report", response_model=CompanyReportResponse)
async def company_report(request: CompanyRequest):
    try:
        report = generate_company_report(request.company_name)
        return CompanyReportResponse(report=report)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-research", response_model=CompanyWebResearchResult)
async def web_research(request: CompanyRequest):
    """
    Executes the 'company/web-research' prompt with Google Search grounding.
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Received web-research request for: {request.company_name}")
        
        # Prepare variables for the prompt
        variables = {
            "company_name": request.company_name,
            "company_url": request.company_url or "",
            "company_id": request.company_id or "",
            "today": request.today,
        }
        
        # Execute prompt via AIService
        # The prompt configuration in Langfuse should have the schema and tools defined
        # Execute prompt via AIService in a thread pool to avoid blocking the event loop
        import asyncio
        from functools import partial
        
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                ai_service.execute_prompt,
                prompt_name="company/web-research",
                variables=variables,
                label="production",
                user_id=request.company_id
            )
        )
        
        # result should be a dict matching CompanyWebResearchResult
        if not isinstance(result, dict):
            logger.error(f"Expected dict from AIService but got {type(result)}. Content: {result}")
            raise ValueError(f"AI Service returned a non-structured response. Please ensure JSON mode is enabled in Langfuse for 'company/web-research'.")

        return CompanyWebResearchResult(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Web research failed: {str(e)}")
