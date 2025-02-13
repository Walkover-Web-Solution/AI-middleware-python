from fastapi import APIRouter, Request, Depends
from ..controllers.rag_controller import create_vectors, get_vectors_and_text
from ..middlewares.middleware import jwt_middleware
router = APIRouter()


@router.post('/', dependencies=[Depends(jwt_middleware)])
async def create_vertors(request: Request):
    return await create_vectors(request)

@router.post('/query', dependencies=[Depends(jwt_middleware)])
async def get_query(request: Request):
    return await get_vectors_and_text(request)