from ..utils.ai_call_util import call_ai_middleware
from ...configs.constant import bridge_ids

async def handle_gpt_memory(id, user, assistant, purpose, gpt_memory_context):
    try:
        variables = {'threadID': id, 'memory' : purpose, "gpt_memory_context": gpt_memory_context}
        content = assistant.get('data', {}).get('content', "")
        configuration = {"conversation": [{"role": "user", "content": user}, {"role": "assistant", "content": content}]}
        message = "use the function to store the memory if the user message and history is related to the context or is important to store else don't call the function and ignore it. is purpose is not there than think its the begining of the conversation"
        response = await call_ai_middleware(message, bridge_id = bridge_ids['gpt_memory'], variables = variables, configuration = configuration, response_type = "text")
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        return response
    except Exception as err:
        print("Error calling function=>", err)
        return None