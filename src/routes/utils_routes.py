from fastapi import APIRouter, Depends, Request
from src.services.cache_service import clear_cache
from ..middlewares.middleware import jwt_middleware
from src.services.utils.add_data_for_demo import add_data_for_demo_save, get_all_data_for_demo, update_data_for_demo
router = APIRouter()

@router.delete('/redis')
async def clear_redis_cache(request: Request):
    return await clear_cache(request)

@router.post('/demo', dependencies=[Depends(jwt_middleware)])
async def data_add_for_demo(request: Request):
    return await add_data_for_demo_save(request)

@router.get('/all')
async def get_data_for_demo(request: Request):
    return await get_all_data_for_demo(request)

@router.put('/update/{id}')
async def update_data_for_demo(request: Request, id: str):
    return await update_data_for_demo(request, id)
