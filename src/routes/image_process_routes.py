from fastapi import APIRouter, Depends, Request
from ..middlewares.middleware import jwt_middleware
from ..controllers.image_process_controller import image_processing, file_processing
router = APIRouter()


@router.post('/')
async def image(request: Request):
    """Process an image-generation or transformation request without auth."""
    return await image_processing(request)
    
@router.post('/upload', dependencies=[Depends(jwt_middleware)])
async def image(request: Request):
    """Handle authenticated media uploads for downstream processing."""
    return await file_processing(request)
