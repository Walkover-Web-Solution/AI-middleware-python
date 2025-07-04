import json
from config import Config
from src.services.utils.apiservice import fetch
from src.configs.constant import service_name

async def Response_formatter(response = {}, service = None, tools={}, type='chat', images = None):
    tools_data = tools
    if isinstance(tools_data, dict):
                for key, value in tools_data.items():
                    if isinstance(value, str):
                        try:
                            tools_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                        
    if service == service_name['openai'] and (type !='image' and type != 'embedding'):
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None),
                "cached_tokens" : response.get("usage", {}).get("prompt_tokens_details",{}).get('cached_tokens')

            }
        }
    elif service == service_name['openai'] and type == 'embedding':
         return {
            "data" : {
                "embedding" : response.get('data')[0].get('embedding')
            }
        }
    
    elif service == service_name['openai']:
        return {
            "data" : {
                "revised_prompt" : response.get('data')[0].get('revised_prompt'),
                "image_url" : response.get('data')[0].get('url')
            }
        }
    
    elif service == service_name['anthropic']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("content", [{}])[0].get("text", None),
                "model" : response.get("model", None),
                "role" : response.get("role", None),
                "finish_reason" : response.get("stop_reason", None),
                "tools_data": tools_data or {},
                "fall_back" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("input_tokens", None),
                "output_tokens" : response.get("usage", {}).get("output_tokens", None),
                "cache_read_input_tokens" : response.get("usage",{}).get("cache_read_input_tokens",None),
                "cache_creation_input_tokens" : response.get("usage",{}).get("cache_creation_input_tokens",None),

                "total_tokens" : (
                    response.get("usage", {}).get("input_tokens", 0) + 
                    response.get("usage", {}).get("output_tokens", 0)
                )
            }
        }
    elif service == service_name['groq']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {},
                "fall_back" : response.get('fallback') or False
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None)
            }
        }
    if service == service_name['openai_response'] and (type != 'image' and type != 'embedding'):
        return {
            "data": {
                "id": response.get("id", None),
                "content": (
                    response.get("output", [{}])[0].get("content", [{}])[0].get("text", None)
                    if response.get("output", [{}])[0].get("type") == "function_call"
                    else next(
                        (item.get("content", [{}])[0].get("text", None)
                         for item in response.get("output", [])
                         if item.get("type") == "message"),
                        None
                    )
                ),
                "model": response.get("model", None),
                "role": 'assistant',
                "status": response.get("status", None),
                "tools_data": tools_data or {},
                "images": images,
                "annotations": response.get("output", [{}])[0].get("content", [{}])[0].get("annotations", None),
                "fall_back" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage": {
                "input_tokens": response.get("usage", {}).get("input_tokens", None),
                "output_tokens": response.get("usage", {}).get("output_tokens", None),
                "total_tokens": response.get("usage", {}).get("total_tokens", None),
                "cached_tokens": response.get("usage", {}).get("input_tokens_details", {}).get('cached_tokens', None)
            }
        }
    elif service == service_name['openai_response'] and type == 'embedding':
        return {
            "data": {
                "embedding": response.get('data')[0].get('embedding')
            }
        }
    
    elif service == service_name['openai_response']:
        return {
            "data": {
                "revised_prompt": response.get('data')[0].get('revised_prompt'),
                "image_url": response.get('data')[0].get('url')
            }
        }
    elif service == service_name['open_router']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None),
                "cached_tokens": (
                    response.get("usage", {})
                    .get("prompt_tokens_details", {}) or {}
                ).get('cached_tokens')

            }
        }
    elif service == service_name['mistral']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None),
                "cached_tokens": (
                    response.get("usage", {})
                    .get("prompt_tokens_details", {}) or {}
                ).get('cached_tokens')

            }
        }

async def validateResponse(alert_flag, configration, bridgeId, message_id, org_id):
    if alert_flag:
        await send_alert(data={"response":"\n..\n","configration":configration,"message_id":message_id,"bridge_id":bridgeId, "org_id": org_id, "message": "\n issue occurs"})

async def send_alert(data):
    dataTosend = {**data, "ENVIROMENT":Config.ENVIROMENT} if Config.ENVIROMENT else data
    await fetch("https://flow.sokt.io/func/scriYP8m551q",method='POST',json_body=dataTosend)