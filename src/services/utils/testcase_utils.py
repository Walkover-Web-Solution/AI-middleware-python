from src.services.commonServices.baseService.baseService import BaseService
import json
import uuid

def add_prompt_and_conversations(custom_config, conversations, service, prompt):
    custom_config['messages'] = custom_messages(custom_config, MakeConversationsAsPerService(conversations), service, prompt)
    base_service = BaseService({})
    return base_service.service_formatter(custom_config, service)

def MakeConversationsAsPerService(conversations, service):
    Newconversations = []
    for conversation in conversations:    
        match service:
            case 'openai' | 'groq':
                if conversation.role == 'tools_call':
                    id =  f"call_{uuid.uuid4().hex[:6]}"
                    for i, tools in enumerate(conversation.content):
                        convers = {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                            {
                                "id": f"{id}{i}{j}",
                                "type": "function",
                                "function": {
                                "name": tool.name,
                                "arguments": json.dumps(tool.args)
                                }
                            } for j, tool in enumerate(tools)
                            ]
                        }
                        Newconversations.append(convers)
                        for i, tools in enumerate(conversation.content):
                             for j, tool in enumerate(tools):
                                conversResponse = {
                                    "role": "tool",
                                    "content": json.dumps({
                                            "response": tool.response,
                                            "metadata": tool.metadata,
                                            "status": tool.status
                                        }),
                                    "tool_call_id": f"{id}{i}{j}"
                                }
                                Newconversations.append(conversResponse)
                else:
                    Newconversations.append(conversation)
            case 'anthropic':
                if conversation.role == 'tools_call':
                    id =  f"toolu_{uuid.uuid4().hex[:6]}"
                    for i, tools in enumerate(conversation.content):
                        convers = {
                            "role": "assistant",
                            "content":  [
                                    {
                                        "type": "text",
                                        "text": "Call the function for better response"
                                    },
                            {
                                "id": f"{id}{i}{j}",
                                "type": "tool_use",
                                "name": tool.name,
                                "input": tool.args
                            } for j, tool in enumerate(tools)
                            ]
                        }
                        Newconversations.append(convers)
                        for i, tools in enumerate(conversation.content):
                            conversResponse = {
                                "role": "user",
                                "content": [
                                    {
                                        "id": f"{id}{i}{j}",
                                        "type": "tool_result",
                                        "content": json.dumps({
                                            "response": tool.response,
                                            "metadata": tool.metadata,
                                            "status": tool.status
                                        })
                                    } for j, tool in enumerate(tools)
                                ]
                            }
                            Newconversations.append(conversResponse)
                else:
                    Newconversations.append(conversation)

    return Newconversations


def custom_messages(custom_config, conversations, service, prompt):
    messages = []
    match service:
            case 'openai':
                messages = [ {"role": "developer", "content": prompt }] + conversations
            case 'anthropic':
                custom_config['system'] = prompt
                messages =  conversations
            case 'groq': 
                messages = [{"role": "system", "content": prompt}] + conversations
    return messages
    
def make_json_serializable(data):
    """Recursively converts non-serializable values in a dictionary to strings."""
    if isinstance(data, dict):
        return {k: make_json_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_serializable(v) for v in data]
    try:
        json.dumps(data)  # Check if serializable
        return data
    except (TypeError, OverflowError):
        return str(data)