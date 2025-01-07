from fastapi import APIRouter, Request
from src.services.cache_service import clear_cache
router = APIRouter()


@router.delete('/redis')
async def clear_redis_cache():
    return await clear_cache()
