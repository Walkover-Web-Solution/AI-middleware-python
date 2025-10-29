from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from src.services.commonServices.bridgeServices import optimize_prompt_controller, generate_summary, function_agrs_using_ai, generate_additional_test_cases
router = APIRouter()

@router.post('/{bridge_id}/optimize/prompt', dependencies=[Depends(jwt_middleware)])
async def update_apicalls(request: Request, bridge_id: str):
    return await optimize_prompt_controller(request, bridge_id)

@router.post('/{bridge_id}/generateAdditionalTestCases', dependencies=[Depends(jwt_middleware)])
async def generate_n_additional_test_cases(request: Request, bridge_id: str):
    return await generate_additional_test_cases(request, bridge_id)

@router.post('/summary', dependencies=[Depends(jwt_middleware)])
async def generate_brideg_summary(request: Request):
    return await generate_summary(request)

@router.post('/genrate/rawjson', dependencies=[Depends(jwt_middleware)])
async def function_args(request: Request):
    return await function_agrs_using_ai(request)