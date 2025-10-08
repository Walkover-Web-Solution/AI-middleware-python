from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.prebuilt_prompt_controller import (
    get_prebuilt_prompts_controller,
    update_prebuilt_prompt_controller,
    reset_prebuilt_prompts_controller,
    get_specific_prebuilt_prompt_controller
)

router = APIRouter()

@router.get('', dependencies=[Depends(jwt_middleware)])
async def get_prebuilt_prompts(request: Request):
    """Get all prebuilt prompts for the organization"""
    return await get_prebuilt_prompts_controller(request)

@router.put('', dependencies=[Depends(jwt_middleware)])
async def update_prebuilt_prompt(request: Request):
    """Update prebuilt prompts with key-value pairs"""
    return await update_prebuilt_prompt_controller(request)

@router.post('/reset', dependencies=[Depends(jwt_middleware)])
async def reset_prebuilt_prompts(request: Request):
    """Reset a specific prebuilt prompt to its original AI middleware value"""
    return await reset_prebuilt_prompts_controller(request)

@router.post('/get-specific', dependencies=[Depends(jwt_middleware)])
async def get_specific_prebuilt_prompt(request: Request):
    """Get a specific prebuilt prompt by prompt_key"""
    return await get_specific_prebuilt_prompt_controller(request)