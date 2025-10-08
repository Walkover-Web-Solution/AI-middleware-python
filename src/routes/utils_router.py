from typing import Optional


from fastapi import APIRouter, Depends, Query, Request
from src.services.cache_service import clear_cache, find_in_cache
from ..services.utils.formatter.ai_middleware_chat_api import (
    improve_prompt_optimizer,
    retrieve_gpt_memory as retrieve_gpt_memory_service,
    structured_output_optimizer,
)
from ..middlewares.middleware import jwt_middleware

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


@router.get('/gpt-memory', dependencies=[Depends(jwt_middleware)])
async def retrieve_gpt_memory(
    _request: Request,
    bridge_id: str = Query(..., min_length=1),
    thread_id: str = Query(..., min_length=1),
    sub_thread_id: str = Query(..., min_length=1),
    version_id: Optional[str] = Query(None),
):
    return await retrieve_gpt_memory_service(
        bridge_id=bridge_id,
        thread_id=thread_id,
        sub_thread_id=sub_thread_id,
        version_id=version_id,
    )
    
@router.post('/improve_prompt')
async def improve_prompt(request: Request):
    return await improve_prompt_optimizer(request)
