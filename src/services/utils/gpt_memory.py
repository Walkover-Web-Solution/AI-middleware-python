import json
from ..utils.ai_call_util import call_ai_middleware
from ...configs.constant import bridge_ids
from globals import *
from src.services.cache_service import store_in_cache

async def handle_gpt_memory(id, user, assistant, purpose, gpt_memory_context):
    try:
        variables = {'threadID': id, 'memory' : purpose, "gpt_memory_context": gpt_memory_context}
        content = assistant.get('data', {}).get('content', "")
        configuration = {"conversation": [{"role": "user", "content": user}, {"role": "assistant", "content": content}]}
        message = "use the function to store the memory if the user message and history is related to the context or is important to store else don't call the function and ignore it. is purpose is not there than think its the begining of the conversation. Only return the exact memory as output no an extra text jusy memory if present or Just return False"
        response = await call_ai_middleware(message, bridge_id = bridge_ids['gpt_memory'], variables = variables, configuration = configuration, response_type = "text")
        if isinstance(response, str) and response != "False":
            await store_in_cache( f"gpt_memory_{id}", response)
        return response
    except Exception as err:
        logger.error(f'Error calling function handle_gpt_memory =>, {str(err)}')