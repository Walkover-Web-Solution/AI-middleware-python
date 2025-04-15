from fastapi import APIRouter, Request
from src.services.cache_service import clear_cache, find_in_cache
router = APIRouter()


@router.delete('/redis')
async def clear_redis_cache(request: Request):
    return await clear_cache(request)

@router.get('/redis/{id}')
async def get_redis_cache(request: Request,id:str):
    return await find_in_cache(id)