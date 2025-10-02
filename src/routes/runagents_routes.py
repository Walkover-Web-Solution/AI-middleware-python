from fastapi import APIRouter, Depends, Request
from src.middlewares.agentsMiddlewares import  agents_auth
from src.controllers.runAgentsController import login_public_user
from src.controllers.configController import get_all_agents, get_agent
from src.middlewares.middleware import jwt_middleware

router = APIRouter()


@router.post("/public/login")
async def login_user(request: Request):
   """Authenticate a public agent user and return session details."""
   result = await login_public_user(request)
   return result

@router.post("/login", dependencies=[Depends(jwt_middleware)])
async def login_user(request: Request):
   """Authenticate an internal agent user via JWT-protected route."""
   result = await login_public_user(request)
   return result

@router.get("/all", dependencies=[Depends(agents_auth)])
async def getAllAgents(request: Request):
   """List agent configurations accessible to the caller."""
   result = await get_all_agents(request)
   return result

@router.get("/{slug_name}", dependencies=[Depends(agents_auth)])
async def getAgent(request: Request, slug_name: str):
   """Fetch a single agent configuration identified by `slug_name`."""
   result = await get_agent(request, slug_name)
   return result
