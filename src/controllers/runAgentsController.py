import json
import uuid
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from ..db_services import ConfigurationServices
from config import Config
from ..routes.v2.modelRouter import chat_completion
from src.middlewares.getDataUsingBridgeId import add_configuration_data_to_body
from src.services.commonServices.generateToken import generateToken
async def get_agent_data(request: Request, agent: str):
    try:
        body = await request.json()
        profile = request.state.profile
        message = body.get("message")
        userId = profile['user']['id']

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
        body = await request.json()
        userId = body.get('userId') or str(uuid.uuid4())
        ispublic = False if body.get('userId') else True
        return generateToken({'userId':userId, 'ispublic': ispublic}, Config.PUBLIC_CHATBOT_TOKEN)
    except HTTPException as http_error:
        raise http_error  # Re-raise HTTP exceptions for proper handling
    except Exception as error: 
        return JSONResponse(status_code=400, content={'error': str(error)})

