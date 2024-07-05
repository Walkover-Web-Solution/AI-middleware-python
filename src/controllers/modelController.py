from fastapi import APIRouter, Depends, Request
from src.services.commonServices.common import (
    prochat,
    getchat#, proCompletion, getCompletion, proEmbeddings, getEmbeddings
)
# from middlewares.middleware import middleware

router = APIRouter()

@router.post("/chat/completion")
async def chat_completion(request: Request):
    return await prochat(request)

@router.post("/playground/chat/completion/{bridge_id}")
async def playground_chat_completion(bridge_id: str, request: Request):
    return await getchat(request, bridge_id)
