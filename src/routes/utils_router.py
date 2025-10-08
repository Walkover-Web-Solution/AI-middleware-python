from fastapi import APIRouter, Request
from src.services.cache_service import clear_cache, find_in_cache
from ..services.utils.formatter.ai_middleware_chat_api import improve_prompt_optimizer, improve_prompt_optimizer, structured_output_optimizer

router = APIRouter()

@router.delete('/redis')
async def clear_redis_cache(request: Request):
    return await clear_cache(request)

@router.get('/redis/{id}')
async def get_redis_cache(request: Request, id: str):
    return await find_in_cache(id)

@router.post('/structured_output')
async def structured_output(request: Request):
    return await structured_output_optimizer(request)
    
@router.post('/improve_prompt')
async def improve_prompt(request: Request):
    return await improve_prompt_optimizer(request)
