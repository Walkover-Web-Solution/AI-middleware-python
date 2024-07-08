from fastapi import APIRouter, Depends, Request
from src.services.commonServices.common import (
    prochat,
    getchat#, proCompletion, getCompletion, proEmbeddings, getEmbeddings
)
from ..middlewares.middleware import jwt_middleware

router = APIRouter()

@router.post("/chat/completion", dependencies=[Depends(jwt_middleware)])
async def chat_completion(request: Request):
    return await prochat(request)

@router.post("/playground/chat/completion/{bridge_id}", dependencies=[Depends(jwt_middleware)])
async def playground_chat_completion(bridge_id: str, request: Request):
    return await getchat(request, bridge_id)
