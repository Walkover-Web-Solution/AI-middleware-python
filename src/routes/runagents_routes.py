from fastapi import APIRouter, Depends, Request
from src.middlewares.agentsMiddlewares import  agents_auth
from src.middlewares.ratelimitMiddleware import rate_limit
from src.controllers.runAgentsController import get_agent_data, login_public_user

router = APIRouter()

async def auth_and_rate_limit(request: Request):
    await agents_auth(request)
    await rate_limit(request,key_path='body.limiter_key' , points=10)

@router.post("/{agent}/sendMessage", dependencies=[Depends(auth_and_rate_limit)])
async def send_message(request: Request, agent: str):
   result = await get_agent_data(request, agent)
   return result

@router.post("/login")
async def send_message(request: Request):
   result = await login_public_user(request)
   return result
