from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..db_services import ConfigurationServices
import jwt
from config import Config
from ..routes.v2.modelRouter import chat_completion
import json
from .getDataUsingBridgeId import add_configuration_data_to_body
from ..db_services.conversationDbService import reset_chat_history
from ..services.commonServices.baseService.utils import sendResponse
from ..services.utils.time import Timer

async def send_data_middleware(request: Request, botId: str):
    try:
        body = await request.json()
        org_id = request.state.profile['org']['id']
        slugName = body.get("slugName")
        threadId = body.get("threadId")
        profile = request.state.profile
        message = body.get("message")
        userId = profile['user']['id']
        chatBotId = botId
        flag = body.get("flag") or False
        
        channelId = f"{chatBotId}{threadId.strip() if threadId and threadId.strip() else userId}"

        bridge_response = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)
        bridges = bridge_response['bridges'] if bridge_response['success'] else {}

        if not bridges: 
            raise HTTPException(status_code=400, detail="Invalid bridge Id")

        actions = [
            {
                "actionId": actionId,
                "description": actionDetails.get('description'),
                "type": actionDetails.get('type'),
                "variable": actionDetails.get('variable')
            }
            for actionId, actionDetails in bridges.get('actions', {}).items()
        ]

        if not bridge_response['success']:
            raise HTTPException(status_code=400, detail="Some error occurred")

        request.state.chatbot = {
            "bridge_id": str(bridges.get('_id', '')),
            "user": message,
            "thread_id": threadId,
            "variables": {**body.get('interfaceContextData', {}), **json.loads(profile.get('variables', "{}"))},
            "configuration": {
                 "response_format": {
                    "type": "default",
                    "cred": {}
                } if flag else {
                    "type": "RTLayer",
                    "cred": {
                        "channel": channelId,
                        "ttl": 1,
                        'apikey': Config.RTLAYER_AUTH
                    }
                }
            },
            "chatbot": True,
            "response_type": { 
                "type": "json_object"
            },
            "actions" : actions
        }
        await add_configuration_data_to_body(request=request)
        
        return await chat_completion(request=request)
    except HTTPException as http_error:
        raise http_error  # Re-raise HTTP exceptions for proper handling
    except Exception as error: 
        return JSONResponse(status_code=400, content={'error': str(error)})

async def chat_bot_auth(request: Request):
    timer_obj = Timer()
    timer_obj.start()
    # request.state.timer = timer
    request.state.timer = timer_obj.getTime();
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1] if ' ' in token else token
    
    if not token:
        raise HTTPException(status_code=498, detail="invalid token")
    
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        if decoded_token:
            check_token = jwt.decode(token, Config.CHATBOTSECRETKEY, algorithms=["HS256"])
            if check_token:
                request.state.profile = {
                    "org": {
                        "id": str(check_token['org_id'])
                    },
                    "user": {
                        "id": str(check_token['user_id'])
                    },
                }
                if check_token.get('variables') is not None:
                    request.state.profile["variables"]: check_token['variables']
                return True
        raise HTTPException(status_code=401, detail="unauthorized user")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="unauthorized user: token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="unauthorized user")

async def reset_chatBot(request: Request, botId: str):
    body = await request.json()
    thread_id = body.get('thread_id')
    profile = request.state.profile
    userId = profile['user']['id']
    org_id = request.state.profile['org']['id']
    slugName = body.get("slugName")
    
    bridge_response = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)
    bridges = bridge_response['bridges'] if bridge_response['success'] else {}
    if not bridges: 
        raise HTTPException(status_code=400, detail="Invalid bridge Id")
    else:
        bridge_id = str(bridges.get('_id', ''))
    result = await reset_chat_history(org_id, bridge_id, thread_id)
    response_format = {
        "type": "RTLayer",
        "cred": {
            "channel": f"{botId}{thread_id.strip() if thread_id and thread_id.strip() else userId}",
            "ttl": 1,
            'apikey': Config.RTLAYER_AUTH
        }
    }
    response = {
        "data": {
            "role": "reset"
        }
    }
    if result['success']:
        await sendResponse(response_format, response, True)
        return JSONResponse(status_code=200, content={'success': True, 'message': 'Chatbot reset successfully'})
    else:
        return JSONResponse(status_code=400, content={'success': False, 'message': 'Error resetting chatbot'})
