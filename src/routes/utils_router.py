from fastapi import APIRouter, Request
from src.services.cache_service import clear_cache, find_in_cache
from ..services.utils.formatter.ai_middleware_chat_api import structured_output_optimizer

router = APIRouter()

@router.delete('/redis')
async def clear_redis_cache(request: Request):
    """Flush cached entries associated with the organisation from Redis."""
    return await clear_cache(request)

@router.get('/redis/{id}')
async def get_redis_cache(request: Request, id: str):
    """Return the cached payload stored under the provided `id`."""
    return await find_in_cache(id)

@router.post('/structured_output')
async def structured_output(request: Request):
    """Normalise a model response into the platform's structured output schema."""
    return await structured_output_optimizer(request)
