from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from src.services.commonServices.common import chat, embedding, batch, run_testcases, image, orchestrator_chat
from src.services.commonServices.baseService.utils import make_request_data
from ...middlewares.middleware import jwt_middleware
from ...middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from concurrent.futures import ThreadPoolExecutor
from config import Config
from src.services.commonServices.queueService.queueService import queue_obj
from src.middlewares.ratelimitMiddleware import rate_limit
from models.mongo_connection import db
from globals import *
from ...db_services.embedUserLimitService import EmbedUserLimitService, extract_cost_from_response

router = APIRouter()

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

async def auth_and_rate_limit(request: Request):
    await jwt_middleware(request)
    await rate_limit(request,key_path='body.bridge_id' , points=100)
    await rate_limit(request,key_path='body.thread_id', points=20)

async def track_embed_user_cost(request: Request, api_endpoint: str, api_function, *args, **kwargs):
    """Wrapper function to track costs for embed users"""
    # Check if this is an embed user
    is_embed_user = getattr(request.state, 'is_embed_user', False)
    org_id = request.state.org_id
    user_id = str(request.state.user_id)
    
    if is_embed_user:
        # Check cost limits before processing
        limit_check = await EmbedUserLimitService.check_cost_limit(org_id, user_id)
        if not limit_check.get('allowed', True):
            return JSONResponse(
                status_code=402,
                content={
                    'error': 'Cost limit exceeded',
                    'message': limit_check.get('reason', 'API usage limit reached'),
                    'current_used': limit_check.get('current_used', 0),
                    'limit': limit_check.get('limit', 0)
                }
            )
    
    # Execute the API function
    result = await api_function(*args, **kwargs)
    
    # Record cost for embed users after successful API call
    if is_embed_user and result:
        try:
            # Extract cost from response
            api_cost = extract_cost_from_response(result, api_endpoint)
            
            # Record usage
            metadata = {
                'folder_id': getattr(request.state, 'folder_id', None),
                'ip': request.client.host if hasattr(request, 'client') else None,
                'version': getattr(request.state, 'version', 2)
            }
            
            await EmbedUserLimitService.record_api_usage(
                org_id=org_id,
                user_id=user_id,
                api_cost=api_cost,
                api_endpoint=api_endpoint,
                metadata=metadata
            )
        except Exception as e:
            # Log error but don't fail the response
            print(f"Error recording API usage: {str(e)}")
    
    return result

@router.post('/chat/completion', dependencies=[Depends(auth_and_rate_limit)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
    
    async def execute_chat_completion():
        data_to_send = await make_request_data(request)
        if db_config.get('orchestrator_id'):
            result = await orchestrator_chat(data_to_send)
            return result
        response_format = data_to_send.get('body',{}).get('configuration', {}).get('response_format', {})
        if response_format and response_format.get('type') != 'default':
            try:
                # Publish the message to the queue
                await queue_obj.publish_message(data_to_send)
                return {"success": True, "message": "Your response will be sent through configured means."}
            except Exception as e:
                # Log the error and return a meaningful error response
                logger.error(f"Failed to publish message: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to publish message.")
        else:
            # Assuming chat is an async function that could be blocking
            type = data_to_send.get("body",{}).get('configuration',{}).get('type')
            if type == 'embedding':
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(executor, lambda: asyncio.run(embedding(data_to_send)))
                return result
            if type == 'image':
                loop = asyncio.get_event_loop()
                result = await image(data_to_send)
                return result
            loop = asyncio.get_event_loop()
            result = await chat(data_to_send)
            return result
    
    return await track_embed_user_cost(request, "chat/completion", execute_chat_completion)


@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(auth_and_rate_limit)])
async def playground_chat_completion_bridge(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2
    
    async def execute_playground_completion():
        if db_config.get('orchestrator_id'):
            result = await orchestrator_chat(request)
            return result
        data_to_send = await make_request_data(request)
        type = data_to_send.get("body",{}).get('configuration',{}).get('type')
        if type == 'embedding':
                result =  await embedding(data_to_send)
                return result
        loop = asyncio.get_event_loop()
        result = await chat(data_to_send)
        return result
    
    return await track_embed_user_cost(request, "playground/chat/completion", execute_playground_completion)

@router.post('/batch/chat/completion', dependencies=[Depends(auth_and_rate_limit)])
async def batch_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    async def execute_batch_completion():
        data_to_send = await make_request_data(request)
        result = await batch(data_to_send)
        return result
    
    return await track_embed_user_cost(request, "batch/chat/completion", execute_batch_completion)


@router.post('/testcases', dependencies=[Depends(auth_and_rate_limit)])
async def run_testcases_route(request: Request):
    """
    Execute testcases either from direct input or MongoDB
    
    This route handles testcase execution with support for:
    - Direct testcase data in request body
    - Fetching testcases from MongoDB by bridge_id or testcase_id
    - Parallel processing of multiple testcases
    - Automatic scoring and history saving
    """
    request.state.is_playground = True
    request.state.version = 2
    
    try:
        # Get request body
        body = await request.json()
        org_id = request.state.profile['org']['id']
        
        # Execute testcases using the service
        from src.services.testcase_service import execute_testcases, TestcaseValidationError, TestcaseNotFoundError
        
        result = await execute_testcases(body, org_id)
        return result
        
    except TestcaseValidationError as ve:
        raise HTTPException(status_code=400, detail={"success": False, "error": str(ve)})
    except TestcaseNotFoundError as nfe:
        # Handle not found cases gracefully
        if "No testcase found for the given testcase_id" in str(nfe):
            return {"success": False, "message": str(nfe), "results": []}
        else:
            return {"success": True, "message": str(nfe), "results": []}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in run_testcases_route: {str(e)}")
        raise HTTPException(status_code=500, detail={"success": False, "error": f"Internal server error: {str(e)}"})