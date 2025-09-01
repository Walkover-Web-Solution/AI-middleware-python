from fastapi import APIRouter, Request, Depends
from ..controllers.rag_controller import (
    create_vectors, get_vectors_and_text, get_all_docs, delete_doc,
    create_vectors_pgvector, get_vectors_and_text_pgvector, get_all_docs_pgvector, delete_doc_pgvector,
    create_vectors_single_table, get_vectors_and_text_single_table, get_all_docs_single_table, delete_doc_single_table
)
from ..middlewares.middleware import jwt_middleware
router = APIRouter()


@router.post('/', dependencies=[Depends(jwt_middleware)])
async def create_vertors(request: Request):
    return await create_vectors(request)

@router.post('/query', dependencies=[Depends(jwt_middleware)])
async def get_query(request: Request):
    return await get_vectors_and_text(request)

@router.get('/docs', dependencies=[Depends(jwt_middleware)])
async def get_docs(request: Request):
    return await get_all_docs(request)

@router.delete('/docs', dependencies=[Depends(jwt_middleware)])
async def delete_org_docs(request: Request):
    return await delete_doc(request)

# PgVector Routes
@router.post('/pgvector', dependencies=[Depends(jwt_middleware)])
async def create_vectors_pgvector_route(request: Request):
    return await create_vectors_pgvector(request)

@router.post('/pgvector/query', dependencies=[Depends(jwt_middleware)])
async def get_query_pgvector_route(request: Request):
    return await get_vectors_and_text_pgvector(request)

@router.get('/pgvector/docs', dependencies=[Depends(jwt_middleware)])
async def get_docs_pgvector_route(request: Request):
    return await get_all_docs_pgvector(request)

@router.delete('/pgvector/docs', dependencies=[Depends(jwt_middleware)])
async def delete_org_docs_pgvector_route(request: Request):
    return await delete_doc_pgvector(request)

# Single Table PgVector Routes (Recommended - Better User Isolation)
@router.post('/pgvector-v2', dependencies=[Depends(jwt_middleware)])
async def create_vectors_single_table_route(request: Request):
    return await create_vectors_single_table(request)

@router.post('/pgvector-v2/query', dependencies=[Depends(jwt_middleware)])
async def get_query_single_table_route(request: Request):
    return await get_vectors_and_text_single_table(request)

@router.get('/pgvector-v2/docs', dependencies=[Depends(jwt_middleware)])
async def get_docs_single_table_route(request: Request):
    return await get_all_docs_single_table(request)

@router.delete('/pgvector-v2/docs', dependencies=[Depends(jwt_middleware)])
async def delete_org_docs_single_table_route(request: Request):
    return await delete_doc_single_table(request)