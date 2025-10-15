from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.image_process_controller import image_processing, file_processing, video_processing
router = APIRouter()


@router.post('/')
async def image(request: Request):
    return await image_processing(request)
    
@router.post('/upload', dependencies=[Depends(jwt_middleware)])
async def image(request: Request):
    return await file_processing(request)

@router.post('/video', dependencies=[Depends(jwt_middleware)])
async def video(request: Request):
    return await video_processing(request)

