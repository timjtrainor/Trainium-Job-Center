from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from ....services.ai.ai_service import AIService
from ....dependencies import get_ai_service

router = APIRouter()

class GenerateStrategyRequest(BaseModel):
    job_description: str
    company_data: Dict[str, Any]
    career_dna: Dict[str, Any]
    job_problem_analysis: Optional[Dict[str, Any]] = None
    vocabulary_mirror: Optional[List[str]] = None
    alignment_strategy: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class GenerateBlueprintRequest(BaseModel):
    job_description: str
    company_data: Dict[str, Any]
    career_dna: Dict[str, Any]
    job_problem_analysis: Optional[Dict[str, Any]] = None
    interviewer_profiles: Optional[List[Dict[str, Any]]] = None
    application_interview_strategy: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class ResearchShadowTruthRequest(BaseModel):
    company_name: str
    topic: str
    context: Optional[str] = None
    user_id: Optional[str] = None

class GeneratePersonaRequest(BaseModel):
    buyer_type: str
    interviewer_title: str
    interviewer_linkedin: str
    application_interview_strategy_json: str
    jd_analysis_json: str
    alignment_strategy_json: str
    previous_interview_context: str
    user_id: Optional[str] = None

class GenerateTMAYRequest(BaseModel):
    primary_anxiety: str
    win_condition: str
    functional_friction_point: str
    mirroring_style: str
    alignment_strategy_json: str
    candidate_dna_summary: str
    user_id: Optional[str] = None

class GenerateQuestionsRequest(BaseModel):
    buyer_type: str
    interviewer_title: str
    interviewer_linkedin: str
    application_interview_strategy_json: str
    jd_analysis_json: str
    user_id: Optional[str] = None

class GenerateTalkingPointsRequest(BaseModel):
    question_text: str
    framework: str
    persona_json: str
    candidate_proof_points: str
    user_id: Optional[str] = None

@router.post("/application-strategy")
async def generate_application_strategy(
    request: GenerateStrategyRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_application_strategy(
            job_description=request.job_description,
            company_data=request.company_data,
            career_dna=request.career_dna,
            job_problem_analysis=request.job_problem_analysis,
            vocabulary_mirror=request.vocabulary_mirror,
            alignment_strategy=request.alignment_strategy,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/blueprint")
async def generate_interview_blueprint(
    request: GenerateBlueprintRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_interview_blueprint(
            job_description=request.job_description,
            company_data=request.company_data,
            career_dna=request.career_dna,
            job_problem_analysis=request.job_problem_analysis,
            interviewer_profiles=request.interviewer_profiles,
            application_interview_strategy=request.application_interview_strategy,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/persona_definition")
async def generate_persona_definition(
    request: GeneratePersonaRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_persona_definition(
            buyer_type=request.buyer_type,
            interviewer_title=request.interviewer_title,
            interviewer_linkedin=request.interviewer_linkedin,
            application_interview_strategy_json=request.application_interview_strategy_json,
            jd_analysis_json=request.jd_analysis_json,
            alignment_strategy_json=request.alignment_strategy_json,
            previous_interview_context=request.previous_interview_context,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tmay")
async def generate_tmay(
    request: GenerateTMAYRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_tmay(
            primary_anxiety=request.primary_anxiety,
            win_condition=request.win_condition,
            functional_friction_point=request.functional_friction_point,
            mirroring_style=request.mirroring_style,
            alignment_strategy_json=request.alignment_strategy_json,
            candidate_dna_summary=request.candidate_dna_summary,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/questions")
async def generate_questions(
    request: GenerateQuestionsRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_questions(
            buyer_type=request.buyer_type,
            interviewer_title=request.interviewer_title,
            interviewer_linkedin=request.interviewer_linkedin,
            application_interview_strategy_json=request.application_interview_strategy_json,
            jd_analysis_json=request.jd_analysis_json,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/talking-points")
async def generate_talking_points(
    request: GenerateTalkingPointsRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = await ai_service.generate_talking_points(
            question_text=request.question_text,
            framework=request.framework,
            persona_json=request.persona_json,
            candidate_proof_points=request.candidate_proof_points,
            user_id=request.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_legacy_strategy(
    request: GenerateStrategyRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    """Legacy endpoint refactored to use generate_application_strategy."""
    return await generate_application_strategy(request, ai_service)

@router.post("/research-shadow-truth")
def research_shadow_truth(
    request: ResearchShadowTruthRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        result = ai_service.research_shadow_truth(
            company_name=request.company_name,
            topic=request.topic,
            context=request.context,
            user_id=request.user_id
        )
        return {"content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
