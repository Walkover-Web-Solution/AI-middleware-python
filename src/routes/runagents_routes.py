from fastapi import APIRouter, Depends, Request
from src.middlewares.agentsMiddlewares import  agents_auth
# from src.middlewares.ratelimitMiddleware import rate_limit
from src.controllers.runAgentsController import login_public_user
from src.controllers.configController import get_all_agents, get_agent
from src.middlewares.middleware import jwt_middleware

router = APIRouter()

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