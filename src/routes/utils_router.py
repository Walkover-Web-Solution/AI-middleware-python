from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from src.services.cache_service import clear_cache, find_in_cache
from ..services.utils.formatter.ai_middleware_chat_api import structured_output_optimizer
from ..services.utils.gpt_memory import get_gpt_memory
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
    bridge_id: str = Query(..., min_length=1),
    thread_id: str = Query(..., min_length=1),
    sub_thread_id: str = Query(..., min_length=1),
    version_id: Optional[str] = Query(None)
):
    bridge_id = bridge_id.strip()
    thread_id = thread_id.strip()
    sub_thread_id = sub_thread_id.strip()
    version_id = version_id.strip() if version_id else None

    if not bridge_id or not thread_id or not sub_thread_id:
        raise HTTPException(status_code=400, detail="bridge_id, thread_id and sub_thread_id are required")

    memory_id, memory = await get_gpt_memory(
        bridge_id=bridge_id,
        thread_id=thread_id,
        sub_thread_id=sub_thread_id,
        version_id=version_id
    )

    return {
        "bridge_id": bridge_id,
        "thread_id": thread_id,
        "sub_thread_id": sub_thread_id,
        "version_id": version_id,
        "memory_id": memory_id,
        "found": memory is not None,
        "memory": memory
    }
