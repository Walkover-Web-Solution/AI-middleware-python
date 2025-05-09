from .apiservice import fetch
import json
from config import Config
import jwt

def generate_token(payload, accesskey):
        return jwt.encode(payload, accesskey)

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

async def call_gtwy_agent(args):
    try:
        request_body = {
            "user": args.get('user'),
            "bridge_id": args.get('bridge_id'),
            "variables": args.get('variables') or {}
        }
        
        org_id = args.get('org_id')
        token = generate_token({"org":{'id': str(org_id)},"user":{ 'id' : str(org_id)} }, Config.SecretKey)
        # await jwt_middleware(token)
        response, rs_headers = await fetch(
            f"https://{Config.URL}/api/v2/model/chat/completion",
            "POST",
            {
                "Content-Type": "application/json",
                "Authorization": token
            },
            None,
            request_body
        )
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        result = response.get('response', {}).get('data', {}).get('content', "")
        result = json.loads(result)
        return result
    except Exception as e:
        raise Exception(f"Error in call_gtwy_agent: {str(e)}")


from fastapi import HTTPException

async def jwt_middleware(token):
    try:
        check_token = jwt.decode(token, Config.SecretKey, algorithms=["HS256"])

        if check_token:
            check_token['org']['id'] = str(check_token['org']['id'])
            check_token['org']['id'] = str(check_token['org']['id'])
            data = check_token
            data2 = str(check_token.get('org', {}).get('id'))
            if isinstance(check_token['user'].get('meta'), str):
                data = False
            else:
                data = check_token['user'].get('meta', {}).get('type', False) == 'embed'
            return data
        
        raise HTTPException(status_code=404, detail="unauthorized user")        
    except Exception as err:
        raise HTTPException(status_code=401, detail="unauthorized user")