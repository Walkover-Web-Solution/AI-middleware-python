import json
from .baseService.utils import sendResponse
from src.services.utils.apiservice import fetch

async def chatbot_suggestions(response_format, assistant, user, prompt):
    try:
        conversations = [{"role": "user", "content": user}, {"role": "assistant", "content": assistant.get('data', '').get('content')}]
        variables = {'prompt' : prompt}
        response, rs_headers = await fetch(
            f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
            "POST",
            {
                "pauthkey": "1b13a7a038ce616635899a239771044c",
                "Content-Type": "application/json"
            },
            None,
            {
                "configuration" : conversations,
                "user": "generate suggestions",
                "bridge_id": "674710c9141fcdaeb820aeb8",
                "variables": variables,
            }
        )
        result = response.get('response', {}).get('data', {}).get('content', "")
        await sendResponse(response_format, result, success=True)
            
    except Exception as err:
        print("Error calling function=>", err)
    