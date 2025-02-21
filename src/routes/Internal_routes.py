from fastapi import APIRouter, Request
from ..controllers.internal_controller import create_semantic_chuncking
router = APIRouter()


@router.post('/chunking/semantic/{mongo_id}', dependencies=[])
async def create_chuncking(request: Request,mongo_id: str):
    return await create_semantic_chuncking(request,id=mongo_id)
