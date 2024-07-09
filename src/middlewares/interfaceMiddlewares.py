from fastapi import APIRouter, Depends, Request, HTTPException, Body
from ..db_services import ConfigurationServices
import jwt
from config import Config
from ..services.commonServices import common
import json

async def send_data_middleware(request: Request, botId: str):
    body = await request.json()
    org_id = request.state.org_id
    slugName = body.get("slugName")
    threadId = body.get("threadId")
    profile = request.state.profile
    message = body.get("message")
    userId = profile.get("userId") 
    chatBotId = botId
    
    channelId = f"{chatBotId}{userId}"
    if threadId and threadId.strip():
        channelId = f"{chatBotId}{threadId}"

    bridge_response = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)
    bridges = bridge_response['bridges'] if(bridge_response['success']) else {}

    actions = []
    for actionId, actionDetails in bridges.get('actions', {}).items():
        description = actionDetails.get('description')
        action_type = actionDetails.get('type')
        variable = actionDetails.get('variable')
        actions.append({"actionId": actionId, "description": description, "type": action_type, "variable": variable})
    if not actions:
        actions = "no available action"

    if not bridge_response['success']:
        raise HTTPException(status_code=400, detail="some error occurred")

    request.state.chatbot = True
    request.state.body = {
        "org_id": org_id,
        "bridge_id": bridges.get('_id', '').__str__(),
        "service": "openai",
        "user": message,
        "thread_id": threadId,
        "variables": {**body['interfaceContextData'], "message": message, "actions": actions, **json.loads(profile.get('variables', "{}"))},
        "RTLayer": True,
        "template_id": Config.TEMPLATE_ID,
        "rtlOptions": {
            "channel": channelId,
            "ttl": 1,
        },
    }
    return await common.prochat(request=request)

async def chat_bot_auth(request: Request):
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
                check_token['org_id'] = str(check_token['org_id'])
                request.state.profile = check_token
                request.state.org_id = check_token['org_id']
                if 'user' not in check_token:
                    request.state.profile['viewOnly'] = True
                return True
        raise HTTPException(status_code=401, detail="unauthorized user")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="unauthorized user: token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="unauthorized user")
