<<<<<<< Updated upstream
async def  Response_formatter(response, service):
=======
from src.services.utils.apiservice import fetch
import json

async def Response_formatter(response, service, tools={}):
    tools_data = tools
    if isinstance(tools_data, dict):
                for key, value in tools_data.items():
                    if isinstance(value, str):
                        try:
                            tools_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                        
>>>>>>> Stashed changes
    if service == 'openai':
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {}
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None),
                "cached_tokens" : response.get("usage", {}).get("prompt_tokens_details",{}).get('cached_tokens')

            }
        }
    
    elif service == 'anthropic':
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("content", [{}])[0].get("text", None),
                "model" : response.get("model", None),
                "role" : response.get("role", None),
                "finish_reason" : response.get("stop_reason", None),
                "tools_data": tools_data or {}
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("input_tokens", None),
                "output_tokens" : response.get("usage", {}).get("output_tokens", None),
                "total_tokens" : (
                    response.get("usage", {}).get("input_tokens", 0) + 
                    response.get("usage", {}).get("output_tokens", 0)
                )
            }
        }
    elif service == 'groq':
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {}
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None)
            }
        }
