from fastapi import APIRouter
from app.services.crewai import get_personal_brand_crew


router = APIRouter(tags=["Personal Branding"])


@router.post("/personal-brand")
async def personal_branding():
    crew = get_personal_brand_crew().crew()
    result = crew.kickoff(inputs={"Job": "Product Manager"})
    return {"personal_branding_document": result.raw}

