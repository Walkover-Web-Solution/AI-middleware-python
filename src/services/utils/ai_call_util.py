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
        
        # Add thread_id and sub_thread_id if provided
        if args.get('thread_id'):
            request_body["thread_id"] = args.get('thread_id')
        if args.get('sub_thread_id'):
            request_body["sub_thread_id"] = args.get('sub_thread_id')
        
        org_id = args.get('org_id')
        token = generate_token({"org":{'id': str(org_id)},"user":{ 'id' : str(org_id)} }, Config.SecretKey)
        url = (
                f"http://localhost:8080/api/v2/model/chat/completion"
                if Config.ENVIROMENT and Config.ENVIROMENT.upper() == "LOCAL"
                else f"https://dev-api.gtwy.ai/api/v2/model/chat/completion"
                if Config.ENVIROMENT and Config.ENVIROMENT.upper() == "TESTING"
                else f"https://api.gtwy.ai/api/v2/model/chat/completion"
            )
        header = {
                "Content-Type": "application/json",
                "Authorization": token
            }
        response, rs_headers = await fetch(url=url,method="POST",headers=header,json_body=request_body)
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        result = response.get('response', {}).get('data', {}).get('content', "")
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return { "data" : result }
    except Exception as e:
        raise Exception(f"Error in call_gtwy_agent: {str(e)}")
