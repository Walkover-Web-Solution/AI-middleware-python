from src.services.commonServices.baseService.baseService import BaseService
import json
import uuid

def add_prompt_and_conversations(custom_config, conversations, service, prompt):
    messages = custom_messages(custom_config, make_conversations_as_per_service(conversations, service), service, prompt)
    
    # For OpenAI, messages are set directly in custom_config['input'], so don't override
    if service != 'openai' and messages:
        custom_config['messages'] = messages
    
    base_service = BaseService({})
    return base_service.service_formatter(custom_config, service)

def make_conversations_as_per_service(conversations, service):
    Newconversations = []
    for conversation in conversations:    
        match service:
            case 'openai':
                if conversation.get('role') == 'tools_call':
                    # For OpenAI new format, skip tool calls as they're not supported in input format
                    # Tool calls should be handled differently in the new OpenAI format
                    continue
            case 'groq' | 'open_router' | 'mistral' | 'gemini' | 'ai_ml':
                if conversation.get('role') == 'tools_call':
                    id =  f"call_{uuid.uuid4().hex[:6]}"
                    for i, tools in enumerate(conversation.get('content')):
                        # Handle case where tools might be a string (parse it) or already a list
                        if isinstance(tools, str):
                            try:
                                tools = json.loads(tools)
                            except json.JSONDecodeError:
                                print(f"Warning: Could not parse tools content: {tools}")
                                continue
                        
                        # Ensure tools is a list
                        if not isinstance(tools, list):
                            tools = [tools]
                            
                        convers = {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                            {
                                "id": f"{id}{i}{j}",
                                "type": "function",
                                "function": {
                                "name": tool.get('name', '') if isinstance(tool, dict) else str(tool),
                                "arguments": json.dumps(tool.get('args', {}) if isinstance(tool, dict) else {})
                                }
                            } for j, tool in enumerate(tools)
                            ]
                        }
                        Newconversations.append(convers)
                        for j, tool in enumerate(tools):
                            conversResponse = {
                                "role": "tool",
                                "content": json.dumps({
                                        "response": tool.get('response', '') if isinstance(tool, dict) else '',
                                        "metadata": tool.get('metadata', {}) if isinstance(tool, dict) else {},
                                        "status": tool.get('status', 'success') if isinstance(tool, dict) else 'success'
                                    }),
                                "tool_call_id": f"{id}{i}{j}"
                            }
                            Newconversations.append(conversResponse)
                else:
                    # Ensure content is not null for regular conversations
                    safe_conversation = conversation.copy()
                    if safe_conversation.get('content') is None:
                        safe_conversation['content'] = ""
                    Newconversations.append(safe_conversation)
            case 'anthropic':
                if conversation.get('role') == 'tools_call':
                    id =  f"toolu_{uuid.uuid4().hex[:6]}"
                    for i, tools in enumerate(conversation.get('content')):
                        # Handle case where tools might be a string (parse it) or already a list
                        if isinstance(tools, str):
                            try:
                                tools = json.loads(tools)
                            except json.JSONDecodeError:
                                print(f"Warning: Could not parse tools content: {tools}")
                                continue
                        
                        # Ensure tools is a list
                        if not isinstance(tools, list):
                            tools = [tools]
                            
                        convers = {
                                "role": "assistant",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": "Call the function for better response"
                                    },
                                    *[{
                                        "id": f"{id}{i}{j}",
                                        "type": "tool_use",
                                        "name": tool.get('name', '') if isinstance(tool, dict) else str(tool),
                                        "input": tool.get('args', {}) if isinstance(tool, dict) else {}
                                    } for j, tool in enumerate(tools)]
                                ]
                                }
                        Newconversations.append(convers)
                        conversResponse = {
                            "role": "user",
                            "content": [
                                {
                                    "tool_use_id": f"{id}{i}{j}",
                                    "type": "tool_result",
                                    "content": json.dumps({
                                        "response": tool.get('response', '') if isinstance(tool, dict) else '',
                                        "metadata": tool.get('metadata', {}) if isinstance(tool, dict) else {},
                                        "status": tool.get('status', 'success') if isinstance(tool, dict) else 'success'
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
                # OpenAI new format uses 'input' with structured content
                developer = [{"role": "developer", "content": prompt}]
                
                # Convert conversations to new OpenAI format
                formatted_conversations = []
                for conv in conversations:
                    # Ensure content is not None/null - provide default empty string
                    content_text = conv.get('content') or ""
                    
                    if conv['role'] == 'assistant':
                        # Assistant messages use output_text
                        formatted_conv = {
                            'role': conv['role'],
                            'content': [{"type": "output_text", "text": content_text}]
                        }
                    else:
                        # User messages use input_text
                        formatted_conv = {
                            'role': conv['role'],
                            'content': [{"type": "input_text", "text": content_text}]
                        }
                    formatted_conversations.append(formatted_conv)
                
                messages = developer + formatted_conversations
                # Set as 'input' for OpenAI new format
                custom_config['input'] = messages
                return []  # Return empty since we set custom_config['input']
                
            case 'anthropic':
                custom_config['system'] = prompt
                messages =  conversations
            case 'groq' | 'open_router' | 'mistral' | 'gemini' | 'ai_ml': 
                messages = [{"role": "system", "content": prompt}] + conversations
    return messages
    