from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.file_processing_controller import file_processing
router = APIRouter()


@router.post('/')
async def file(request: Request):
    return await file_processing(request)
