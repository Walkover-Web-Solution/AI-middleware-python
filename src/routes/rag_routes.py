from fastapi import APIRouter, Request
from ..controllers.rag_controller import create_vectors
router = APIRouter()


@router.post('/')
async def create_vertors(request: Request):
    return await create_vectors(request)

@router.post('/query')
async def get_query(request: Request):
    return await create_vectors(request)