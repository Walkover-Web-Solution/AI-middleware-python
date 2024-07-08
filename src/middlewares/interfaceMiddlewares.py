from fastapi import APIRouter, Depends, Request, HTTPException
from ..db_services import ConfigurationServices

async def send_data_middleware(request: Request, body: Body, profile: Profile, botId: str):
    org_id = body.org_id
    slugName = body.slugName
    threadId = body.threadId
    message = body.message
    userId = profile.userId
    chatBotId = botId

    channelId = f"{chatBotId}{userId}"
    if threadId and threadId.strip():
        channelId = f"{chatBotId}{threadId}"

    bridges, success = await ConfigurationServices.get_bridge_by_slugname(org_id, slugName)

    actions = []
    for actionId, actionDetails in bridges.get('actions', {}).items():
        description = actionDetails.get('description')
        action_type = actionDetails.get('type')
        variable = actionDetails.get('variable')
        actions.append({"actionId": actionId, "description": description, "type": action_type, "variable": variable})

    if not actions:
        actions = "no available action"

    if not success:
        raise HTTPException(status_code=400, detail="some error occurred")

    request.state.chatbot = True
    request.state.body = {
        "org_id": org_id,
        "bridge_id": bridges.get('_id', '').__str__(),
        "service": "openai",
        "user": message,
        "thread_id": threadId,
        "variables": {**body.interfaceContextData, "message": message, "actions": actions, **profile.variables},
        "RTLayer": True,
        "template_id": "process.env.TEMPLATE_ID",
        "rtlOptions": {
            "channel": channelId,
            "ttl": 1,
        },
    }