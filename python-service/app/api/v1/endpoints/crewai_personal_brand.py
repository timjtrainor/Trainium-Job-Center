from fastapi import APIRouter, Depends
from ....services.crewai import PersonalBrandCrew, get_personal_brand_crew


router = APIRouter(tags=["Personal Branding"])


@router.post("/personal-brand")
async def personal_branding(
    personal_brand_crew: PersonalBrandCrew = Depends(get_personal_brand_crew),
):
    crew = personal_brand_crew.crew()
    result = crew.kickoff(inputs={"Job": "Product Manager"})
    return {"personal_branding_document": result.raw}

