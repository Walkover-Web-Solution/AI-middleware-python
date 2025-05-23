from fastapi import APIRouter, Depends, Request
from src.middlewares.agentsMiddlewares import  agents_auth
# from src.middlewares.ratelimitMiddleware import rate_limit
from src.controllers.runAgentsController import login_public_user
from src.controllers.configController import get_all_agents, get_agent
from src.middlewares.middleware import jwt_middleware

router = APIRouter()

# async def auth_and_rate_limit(request: Request):
#     await agents_auth(request)
#     await rate_limit(request,key_path='body.limiter_key' , points=10)

# @router.post("/{agent}/sendMessage", dependencies=[Depends(auth_and_rate_limit)])
# async def send_message(request: Request, agent: str):
#    result = await get_agent_data(request, agent)
#    return result

@router.post("/public/login")
async def login_user(request: Request):
   result = await login_public_user(request)
   return result

@router.post("/login", dependencies=[Depends(jwt_middleware)])
async def login_user(request: Request):
   result = await login_public_user(request)
   return result

@router.get("/all", dependencies=[Depends(agents_auth)])
async def getAllAgents(request: Request):
   result = await get_all_agents(request)
   return result

@router.get("/{slug_name}", dependencies=[Depends(agents_auth)])
async def getAgent(request: Request, slug_name: str):
   result = await get_agent(request, slug_name)
   return result