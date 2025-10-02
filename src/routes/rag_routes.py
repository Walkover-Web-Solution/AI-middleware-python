from fastapi import APIRouter, Request, Depends
from ..controllers.rag_controller import create_vectors, get_vectors_and_text, get_all_docs, delete_doc
from ..middlewares.middleware import jwt_middleware
router = APIRouter()


@router.post('/', dependencies=[Depends(jwt_middleware)])
async def create_vertors(request: Request):
    """Create vector embeddings for uploaded documents in the caller's workspace."""
    return await create_vectors(request)

@router.post('/query', dependencies=[Depends(jwt_middleware)])
async def get_query(request: Request):
    """Run a semantic query against stored document vectors."""
    return await get_vectors_and_text(request)

@router.get('/docs', dependencies=[Depends(jwt_middleware)])
async def get_docs(request: Request):
    """List documents and associated metadata for the authenticated organisation."""
    return await get_all_docs(request)

@router.delete('/docs', dependencies=[Depends(jwt_middleware)])
async def delete_org_docs(request: Request):
    """Remove indexed documents belonging to the current organisation."""
    return await delete_doc(request)
