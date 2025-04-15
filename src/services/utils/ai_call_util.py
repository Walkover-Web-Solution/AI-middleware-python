from .apiservice import fetch
import json

async def call_ai_middleware(user, bridge_id, variables = {}, configuration = None, response_type = None, thread_id = None):
    request_body = {
        "user": user,
        "bridge_id": bridge_id,
        "variables": variables
    }
    if response_type is not None:
        request_body["response_type"] = response_type
    
    if configuration is not None:
        request_body["configuration"] = configuration
    
    if thread_id is not None:
        request_body["thread_id"] = thread_id
    
    response, rs_headers = await fetch(
        f"https://api.gtwy.ai/api/v2/model/chat/completion",
        "POST",
        {
            "pauthkey": "1b13a7a038ce616635899a239771044c",
            "Content-Type": "application/json"
        },
        None,
        request_body
    )
    if not response.get('success', True):
        raise Exception(response.get('message', 'Unknown error'))
    result = response.get('response', {}).get('data', {}).get('content', "")
    if response_type is None:
        result = json.loads(result)
    return result