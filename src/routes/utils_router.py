from fastapi import APIRouter, Depends, Request
from src.services.cache_service import clear_cache, find_in_cache
from ..services.utils.formatter.ai_middleware_chat_api import structured_output_optimizer, retrieve_gpt_memory
from ..middlewares.middleware import jwt_middleware

router = APIRouter()

@router.delete('/redis')
async def clear_redis_cache(request: Request):
    return await clear_cache(request)

@router.get('/redis/{id}')
async def get_redis_cache(request: Request, id: str):
    return await find_in_cache(id)

@router.post('/structured_output', dependencies=[Depends(jwt_middleware)])
async def structured_output(request: Request):
    return await structured_output_optimizer(request)


@router.get('/gpt-memory', dependencies=[Depends(jwt_middleware)])
async def retrieve_gpt_memory(request: Request):
    return await retrieve_gpt_memory(request)