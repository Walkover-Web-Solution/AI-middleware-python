from fastapi import APIRouter, Request
from src.services.cache_service import clear_cache, find_in_cache, delete_with_id_prefix
from ..services.utils.formatter.ai_middleware_chat_api import structured_output_optimizer

router = APIRouter()

@router.delete('/redis')
async def clear_redis_cache(request: Request):
    return await clear_cache(request)

@router.delete('/redis/{id}')
async def delete_with_id_or_prefix(id: str):
    return await delete_with_id_prefix(id)    

@router.get('/redis/{id}')
async def get_redis_cache(request: Request, id: str):
    return await find_in_cache(id)

@router.post('/structured_output')
async def structured_output(request: Request):
    return await structured_output_optimizer(request)
