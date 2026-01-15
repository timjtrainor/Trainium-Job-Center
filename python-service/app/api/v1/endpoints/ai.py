from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union

from ....services.ai.ai_service import AIService
from ....dependencies import get_ai_service

router = APIRouter()

class ExecutePromptRequest(BaseModel):
    prompt_name: str
    variables: Dict[str, Any] = {}
    model_alias: Optional[str] = None
    label: Optional[str] = None
    json_schema: Optional[str] = None # Optional schema string to enforcing JSON structure
    trace_source: Optional[str] = None

@router.post("/execute")
def execute_prompt(
    request: ExecutePromptRequest,
    ai_service: AIService = Depends(get_ai_service)
):
    try:
        # Filter out None values to avoid overwriting Langfuse config
        params = request.dict(exclude_none=True)
        # prompt_name and variables are core
        prompt_name = params.pop("prompt_name")
        variables = params.pop("variables", {})
        
        result = ai_service.execute_prompt(
            prompt_name=prompt_name,
            variables=variables,
            **params
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
