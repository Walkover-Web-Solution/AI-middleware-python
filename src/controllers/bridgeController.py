from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from src.services.commonServices.bridgeServices import optimize_prompt_controller, generate_summary, function_agrs_using_ai
router = APIRouter()

@router.post('/{bridge_id}/optimize/prompt', dependencies=[Depends(jwt_middleware)])
async def update_apicalls(request: Request, bridge_id: str):
    """Optimise a bridge prompt using AI-driven adjustments."""
    return await optimize_prompt_controller(request, bridge_id)

@router.post('/summary', dependencies=[Depends(jwt_middleware)])
async def generate_brideg_summary(request: Request):
    """Generate a concise summary for the supplied bridge configuration."""
    return await generate_summary(request)

@router.post('/genrate/rawjson', dependencies=[Depends(jwt_middleware)])
async def function_args(request: Request):
    """Produce suggested function arguments or payload schema via AI."""
    return await function_agrs_using_ai(request)
