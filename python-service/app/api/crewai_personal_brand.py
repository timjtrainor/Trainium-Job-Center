from fastapi import APIRouter
from app.services.crewai.personal_branding.crew import PersonalBrandCrew

router = APIRouter(tags=["Personal Branding"])

@router.post("/personal-brand")
async def review_job_posting():
    crew = PersonalBrandCrew()
    result = crew.branding_crew().kickoff(inputs={"narrative_name": "Product Manager"})
    return {"personal_branding_document": result}