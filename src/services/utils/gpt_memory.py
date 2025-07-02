import json
from ..utils.ai_call_util import call_ai_middleware
from ...configs.constant import bridge_ids
from globals import *
from src.services.utils.apiservice import fetch
from src.services.cache_service import store_in_cache_permanent_until_read, find_in_cache_and_expire

async def handle_gpt_memory(id, user, assistant, purpose, gpt_memory_context):
    try:
        # First check if we have a cached response - this will expire the key if found
        cached_response = await find_in_cache_and_expire(id)
        if cached_response:
            # If we found a cached response, parse and return it
            return json.loads(cached_response)
            
        # If no cached response, proceed with normal flow
        variables = {'threadID': id, 'memory' : purpose, "gpt_memory_context": gpt_memory_context}
        content = assistant.get('data', {}).get('content', "")
        configuration = {"conversation": [{"role": "user", "content": user}, {"role": "assistant", "content": content}]}
        message = "use the function to store the memory if the user message and history is related to the context or is important to store else don't call the function and ignore it. is purpose is not there than think its the begining of the conversation"
        await call_ai_middleware(message, bridge_id = bridge_ids['gpt_memory'], variables = variables, configuration = configuration, response_type = "text")
        response, _ = await fetch("https://flow.sokt.io/func/scriCJLHynCG", "POST", None, None, {"threadID": id})
        if isinstance(response, str):
            await store_in_cache_permanent_until_read(id, response)
        return response
    except Exception as err:
        logger.error(f'Error calling function handle_gpt_memory =>, {str(err)}')