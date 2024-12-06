from .apiservice import fetch

async def handle_gpt_memory(id, user, assistant):
    try:
        variables = {'threadID': id}
        content = assistant.get('choices', [{}])[0].get('message', {}).get('content', '')
        response, rs_headers = await fetch(
            f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
            "POST",
            {
                "pauthkey": "1b13a7a038ce616635899a239771044c",
                "Content-Type": "application/json"
            },
            None,
            {
                "conversation": [{"role": "user", "content": user}, {"role": "assistant", "content": content}],
                "user": "use the function to store the memory if the user message and history is related to the or important to store else don't call the function and ignore it.",
                "bridge_id": "6752d9fc232e8659b2b65f0d",
                "response_type": "text",
                "variables": variables
            }
        )
        if not response.get('success', True):
            raise Exception(response.get('message', 'Unknown error'))
        return response.get('response', {}).get('data', {}).get('content', "")
    except Exception as err:
        print("Error calling function=>", err)
        return None