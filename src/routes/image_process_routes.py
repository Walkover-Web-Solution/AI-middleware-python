from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.image_process_controller import image_processing
router = APIRouter()


@router.post('/')
async def image(request: Request):
    return await image_processing(request)
