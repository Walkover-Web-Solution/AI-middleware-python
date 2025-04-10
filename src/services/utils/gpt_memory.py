from .apiservice import fetch
from globals import *

async def handle_gpt_memory(id, user, assistant, purpose, gpt_memory_context):
    try:
        variables = {'threadID': id, 'memory' : purpose, "gpt_memory_context": gpt_memory_context}
        content = assistant.get('data', {}).get('content', "")
        response, rs_headers = await fetch(
            f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
            "POST",
            {
                "pauthkey": "1b13a7a038ce616635899a239771044c",
                "Content-Type": "application/json"
            },
            None,
            {
                "configuration" : {"conversation": [{"role": "user", "content": user}, {"role": "assistant", "content": content}]},
                "user": "use the function to store the memory if the user message and history is related to the context or is important to store else don't call the function and ignore it. is purpose is not there than think its the begining of the conversation",
                "bridge_id": "6752d9fc232e8659b2b65f0d",
                "response_type": "text",
                "variables": variables,
                # "thread_id" : id
            }
        )
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        return response.get('response', {}).get('data', {}).get('content', "")
    except Exception as err:
        logger.error(f'Error calling function=>, {str(err)}')