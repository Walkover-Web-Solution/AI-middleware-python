from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..db_services import ConfigurationServices
import jwt
from config import Config
from ..routes.v2.modelRouter import chat_completion
import json
from .getDataUsingBridgeId import add_configuration_data_to_body
from ..db_services.conversationDbService import reset_and_mode_chat_history
from ..services.commonServices.baseService.utils import sendResponse
from ..services.utils.time import Timer
from src.services.utils.apiservice import fetch

async def send_data_middleware(request: Request, botId: str):
    try:
        body = await request.json()
        org_id = request.state.profile['org']['id']
        slugName = body.get("slugName")
        isPublic = 'ispublic' in request.state.profile
        user_email = body.get('state',{}).get("profile",{}).get("user",{}).get("email",'')
        if isPublic:
            threadId = str(request.state.profile['user']['id'])
        else:
            threadId = str(body.get("threadId")) if body.get("threadId") is not None else None
        profile = request.state.profile
        message = (body.get("message") or "").strip()
        userId = profile['user']['id']
        subThreadId = threadId if isPublic and not body.get("subThreadId")  else body.get("subThreadId") 
        chatBotId = botId
        images = body.get("images") or []
        flag = body.get("flag") or False
        if not message and not images:
            return JSONResponse(status_code=400, content={'error': "Message cannot be null"})

        channelId = f"{chatBotId}{threadId.strip() if threadId and threadId.strip() else userId}{subThreadId.strip() if subThreadId and subThreadId.strip() else userId}"
        channelId = channelId.replace(" ", "_")
        if(isPublic):
            bridge_response = await ConfigurationServices.get_agents_data(slugName, user_email)
            org = { "id": bridge_response.get('org_id') }
            request.state.profile["org"] = org
        else:
            bridge_response = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)
        bridges = bridge_response if bridge_response else {}

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
        
        request.state.chatbot = {
            "bridge_id": str(bridges.get('_id', '')),
            "user": message,
            "thread_id": threadId,
            "sub_thread_id":subThreadId,
            "variables": {**body.get('interfaceContextData', {}), **body.get('variables',{}), **json.loads(profile.get('variables', "{}"))},
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
                },
                **body.get('configuration', {}),
                "max_token": bridges.get('max_token', None) if isPublic else None
            },
            "chatbot": True,
            "response_type": { 
                "type": "json_object"
            },
            "actions" : actions,
            "bridge_summary" : bridges.get('bridge_summary')
        }
        await add_configuration_data_to_body(request=request)
        
        return await chat_completion(request=request)
    except HTTPException as http_error:
        raise http_error  # Re-raise HTTP exceptions for proper handling
    except Exception as error: 
        return JSONResponse(status_code=400, content={'error': 'Error: ' + str(error)})

async def chat_bot_auth(request: Request):
    timer_obj = Timer()
    timer_obj.start()
    # request.state.timer = timer
    request.state.timer = timer_obj.getTime()
    is_public_agent = request.path_params.get('botId', None) == "Public_Agents"
    token = request.headers.get('Authorization')
    if token:
        token = token.split(' ')[1] if ' ' in token else token
    
    if not token:
        raise HTTPException(status_code=498, detail="invalid token")
    
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        if decoded_token:
            check_token = jwt.decode(token, Config.PUBLIC_CHATBOT_TOKEN if is_public_agent else Config.CHATBOTSECRETKEY, algorithms=["HS256"])
            if check_token:
                request.state.profile = {
                    "org": {
                        "id": str(check_token['org_id'])
                    },
                    "user": {
                        "id": str(check_token['user_id']),
                        "email": str(check_token.get('userEmail', ""))
                    },
                }
                if check_token.get('variables') is not None:
                    request.state.profile["variables"] = json.dumps(check_token['variables']) if not isinstance(check_token['variables'], str) else check_token['variables']
                if check_token.get('ispublic') is not None:
                    request.state.profile["ispublic"] = check_token['ispublic']
                return True
        raise HTTPException(status_code=401, detail="unauthorized user")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="unauthorized user: token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="unauthorized user")

async def reset_chatBot(request: Request, botId: str):
    body = await request.json()
    thread_id = body.get('thread_id')
    sub_thread_id = body.get('sub_thread_id')
    version_id = body.get("version_id")
    profile = request.state.profile
    userId = profile['user']['id']
    org_id = request.state.profile['org']['id']
    slugName = body.get("slugName")
    purpose = body.get("purpose")
    
    channelId = f"{botId}{thread_id.strip() if thread_id and thread_id.strip() else userId}{sub_thread_id.strip() if sub_thread_id and sub_thread_id.strip() else userId}"
    channelId = channelId.replace(" ", "_")
    bridges = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)
    bridge_id = str(bridges.get('_id', ''))
    if purpose == 'is_reset':
        result = await reset_and_mode_chat_history(org_id, bridge_id, thread_id, 'is_reset', True)
        id = f"{thread_id}_{ version_id or bridge_id}"
        gpt_memory = bridges.get('gpt_momery')
        if gpt_memory:
            response = await fetch("https://flow.sokt.io/func/scrixTV20rkF", "POST", None, None, {"threadID": id})



    response_format = {
            "type": "RTLayer",
        "cred": {
            "channel": channelId,
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
