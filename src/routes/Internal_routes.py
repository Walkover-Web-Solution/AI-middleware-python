from fastapi import APIRouter, Request
from ..controllers.internal_controller import create_semantic_chuncking
router = APIRouter()


@router.get('/chunking/semantic/{mongo_id}', dependencies=[])
async def create_chuncking(request: Request,mongo_id: str):
    """Kick off semantic chunk generation for the document identified by `mongo_id`."""
    return await create_semantic_chuncking(request,id=mongo_id)
