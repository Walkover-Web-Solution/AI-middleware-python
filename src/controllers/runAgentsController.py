import json
import uuid
import hashlib
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..db_services import ConfigurationServices
from config import Config
from ..routes.v2.modelRouter import chat_completion
from src.middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from src.services.commonServices.generateToken import generateToken
async def get_agent_data(request: Request, agent: str): #ignore
    try:
        body = await request.json()
        profile = request.state.profile
        message = body.get("message")
        userId = profile['user']['id']
        subThreadId = body.get("subThreadId")

        flag = body.get("flag") or False
        
        if not message or message == "":
            return JSONResponse(status_code=400, content={'error':"Message cannot be null"})
        
        channelId = f"{agent}_{userId}"
        channelId = channelId.replace(" ", "_")
        
        bridge_response = await ConfigurationServices.get_bridge_by_slugname(agent) # TODO
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
            "thread_id": userId,
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
        return JSONResponse(status_code=400, content={'error': str(error)})

async def login_public_user(request: Request):
    try:
        body = await request.json() if await request.body() else {}
        user_info = body.get('state', {}).get('profile', {}).get('user', {})
        user_id = user_info.get('id')
        user_email = user_info.get('email')
        is_public = not bool(user_email)

        # Attempt to use IP address as fallback user_id
        if not user_id:
            client_host = request.client.host if request.client else None
            if client_host:
                # Hash the IP to create a consistent but anonymized user ID
                user_id = hashlib.sha256(client_host.encode()).hexdigest()
            else:
                user_id = str(uuid.uuid4())  # Fallback to UUID if IP not available

        return {
            "token": generateToken({'userId': user_id, "userEmail": user_email, 'ispublic': is_public}, Config.PUBLIC_CHATBOT_TOKEN),
            "user_id": user_id
        }

    except HTTPException as http_error:
        raise http_error  # Re-raise HTTP exceptions for proper handling
    except Exception as error:
        return JSONResponse(status_code=400, content={'error': str(error)})
