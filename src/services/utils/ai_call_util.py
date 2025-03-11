from .apiservice import fetch

async def call_ai_middleware(user, bridge_id, variables = None, configuration = None, response_type = None, thread_id = None):
    try:
        request_body = {
            "configuration": configuration,
            "user": user,
            "bridge_id": bridge_id,
            "response_type": response_type,
            "variables": variables
        }
        
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
        return response.get('response', {}).get('data', {}).get('content', "")
    except Exception as err:
        print("Error calling function=>", err)
        raise err