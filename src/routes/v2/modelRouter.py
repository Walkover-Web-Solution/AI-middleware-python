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

router = APIRouter()

executor = ThreadPoolExecutor(max_workers= int(Config.max_workers) or 10)

async def auth_and_rate_limit(request: Request):
    await jwt_middleware(request)
    await rate_limit(request,key_path='body.bridge_id' , points=100)
    await rate_limit(request,key_path='body.thread_id', points=20)

@router.post('/chat/completion', dependencies=[Depends(auth_and_rate_limit)])
async def chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = False
    request.state.version = 2
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


@router.post('/playground/chat/completion/{bridge_id}', dependencies=[Depends(auth_and_rate_limit)])
async def playground_chat_completion_bridge(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    request.state.is_playground = True
    request.state.version = 2
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

@router.post('/batch/chat/completion', dependencies=[Depends(auth_and_rate_limit)])
async def batch_chat_completion(request: Request, db_config: dict = Depends(add_configuration_data_to_body)):
    data_to_send = await make_request_data(request)
    result = await batch(data_to_send)
    return result


@router.post('/testcases', dependencies=[Depends(auth_and_rate_limit)])
async def run_testcases_route(request: Request):
    request.state.is_playground = True
    request.state.version = 2
    
    try:
        # Get request body
        body = await request.json()
        bridge_id = body.get('bridge_id')
        version_id = body.get('version_id')
        testcase_id = body.get('testcase_id')
        
        if not bridge_id:
            raise HTTPException(status_code=400, detail={"success": False, "error": "bridge_id is required"})
        
        if not version_id:
            raise HTTPException(status_code=400, detail={"success": False, "error": "version_id is required"})
        
        # Fetch testcases from MongoDB
        testcases_collection = db['testcases']
        
        if testcase_id:
            # Fetch specific testcase by _id
            from bson import ObjectId
            testcase = await testcases_collection.find_one({"_id": ObjectId(testcase_id)})
            if not testcase:
                return {"success": False, "message": "No testcase found for the given testcase_id", "results": []}
            testcases = [testcase]
        else:
            # Fetch all testcases with the given bridge_id
            testcases = await testcases_collection.find({"bridge_id": bridge_id}).to_list(length=None)
            if not testcases:
                return {"success": True, "message": "No testcases found for the given bridge_id", "results": []}
        
        # Manually call the configuration service to get the configuration
        from src.services.utils.getConfiguration import getConfiguration
        
        org_id = request.state.profile['org']['id']
        db_config = await getConfiguration(
            None,
            None,
            bridge_id, 
            None,
            None,
            {},
            org_id, 
            None,
            version_id=version_id, 
            extra_tools=[], 
            built_in_tools=None,
            guardrails=None
        )
        
        if not db_config.get("success"):
            raise HTTPException(status_code=400, detail={"success": False, "error": db_config.get("error", "Failed to get configuration")})
        
        # Process all testcases in parallel
        async def process_testcase(testcase):
            try:
                # Create request data for this testcase
                # Set conversation in db_config
                db_config['configuration']['conversation'] = testcase.get('conversation', [])
                
                testcase_request_data = {
                    "body": {
                        "user": testcase.get('conversation', [])[-1].get('content', '') if testcase.get('conversation') else '',
                        "testcase_data": {
                            "matching_type": testcase.get('matching_type') or 'cosine',
                            "run_testcase": True,
                            "_id": testcase.get('_id'),
                            "expected": testcase.get('expected'),
                            "type": testcase.get('type', 'response')
                        },
                        **db_config
                        
                    },
                    "state": {
                        "is_playground": True,
                        "version": 2
                    }
                }
                
                # Call chat function
                result = await chat(testcase_request_data)
                
                # Extract data from JSONResponse object
                if hasattr(result, 'body'):
                    import json
                    result_data = json.loads(result.body.decode('utf-8'))
                else:
                    result_data = result
                
                print("Result data:", result_data)
                
                # Extract testcase result with score if available
                testcase_result = result_data.get('response', {}).get('testcase_result', {}) if isinstance(result_data, dict) else {}
                
                return {
                    "testcase_id": str(testcase.get('_id')),
                    "bridge_id": testcase.get('bridge_id'),
                    "expected": testcase.get('expected'),
                    "actual_result": result_data.get('response', {}).get('data', {}).get('content', '') if isinstance(result_data, dict) else str(result_data),
                    "score": testcase_result.get('score'),
                    "matching_type": testcase.get('matching_type', ''),
                    "success": True
                }
            except Exception as e:
                logger.error(f"Error processing testcase {testcase.get('_id')}: {str(e)}")
                return {
                    "testcase_id": str(testcase.get('_id')),
                    "bridge_id": testcase.get('bridge_id'),
                    "expected": testcase.get('expected'),
                    "actual_result": None,
                    "score": 0,
                    "matching_type": testcase.get('matching_type', 'cosine'),
                    "error": str(e),
                    "success": False
                }
        
        # Run all testcases in parallel
        results = await asyncio.gather(*[process_testcase(testcase) for testcase in testcases])
        
        return {
            "success": True,
            "bridge_id": bridge_id,
            "version_id": version_id,
            "total_testcases": len(testcases),
            "results": results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in run_testcases_route: {str(e)}")
        raise HTTPException(status_code=500, detail={"success": False, "error": f"Internal server error: {str(e)}"})