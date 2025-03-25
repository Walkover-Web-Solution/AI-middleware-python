from .apiservice import fetch

async def handle_gpt_memory(id, user, ai_config, purpose, gpt_memory_context):
    try:
        variables = {'threadID': id, 'memory' : purpose, "gpt_memory_context": gpt_memory_context}
        messages = ai_config.get('messages', [])
        if(len(messages)> 8 and messages[9].get('role') == 'user'):
            messages.pop(1)
            messages.pop(1)
        content = None
        if len(messages) > 3 and messages[3].get('role') == 'user':
            last3rdUser = extract_content(messages[3])
        if len(messages) > 4 and messages[4].get('role') == 'assistant':
            content = extract_content(messages[4])

        if(content and  len(messages) > 6 and messages[7].get('role') == 'user'): 
            response, rs_headers = await fetch(
                f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
                "POST",
                {
                    "pauthkey": "1b13a7a038ce616635899a239771044c",
                    "Content-Type": "application/json"
                },
                None,
                {
                    "configuration" : {"conversation": [{"role": "user", "content": last3rdUser}, {"role": "assistant", "content": content}]},
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
        else:
            return "No need to make gpt memory"
    except Exception as err:
        print("Error calling function=>", err)
        return None
    

def extract_content(message):
    if isinstance(message.get('content'), list):
        for item in message['content']:
            if item.get('type') == 'text':
                return item.get('text')
        return message['content']  # If 'text' type is not found
    else:
        return message.get('content')
