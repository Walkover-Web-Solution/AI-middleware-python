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
    if service == service_name['openai'] and (type != 'image' and type != 'embedding'):
        return {
            "data": {
                "id": response.get("id", None),
                "content": (
                    # Check if any item in output is a function call
                    next(
                        (f"Function call: {item.get('name', 'unknown')} with arguments: {item.get('arguments', '')}"
                         for item in response.get("output", [])
                         if item.get("type") == "function_call"),
                        None
                    )
                    if any(item.get("type") == "function_call" for item in response.get("output", []))
                    else (
                        # Try to get content from multiple types with fallback
                        next(
                            (item.get("content", [{}])[0].get("text", None)
                             for item in response.get("output", [])
                             if item.get("type") == "message" and item.get("content", [{}])[0].get("text", None) is not None),
                            None
                        ) or
                        next(
                            (item.get("content", [{}])[0].get("text", None)
                             for item in response.get("output", [])
                             if item.get("type") == "output_text" and item.get("content", [{}])[0].get("text", None) is not None),
                            None
                        ) or
                        next(
                            (item.get("content", [{}])[0].get("text", None)
                             for item in response.get("output", [])
                             if item.get("type") == "reasoning" and item.get("content", [{}])[0].get("text", None) is not None),
                            None
                        )
                    )
                ),
                "model": response.get("model", None),
                "role": 'assistant',
                "finish_reason":  finish_reason_mapping(response.get("status", "")) if response.get("status", None) == "in_progress" or response.get("status", None) == "completed" else finish_reason_mapping(response.get("incomplete_details", {}).get("reason", None)) ,
                "tools_data": tools_data or {},
                "images": images,
                "annotations": response.get("output", [{}])[0].get("content", [{}])[0].get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or ''
            },
            "usage": {
                "input_tokens": response.get("usage", {}).get("input_tokens", None),
                "output_tokens": response.get("usage", {}).get("output_tokens", None),
                "total_tokens": response.get("usage", {}).get("total_tokens", None),
                "cached_tokens": response.get("usage", {}).get("input_tokens_details", {}).get('cached_tokens', None)
            }
        }                    
    elif service == service_name['gemini'] and (type !='image' and type != 'embedding' and type != 'video'):
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
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
    elif service == service_name['gemini'] and type == 'image':
        return {
            "data" : {
                "revised_prompt" : response.get('data')[0].get('text_content'),
                "image_url" : response.get('data')[0].get('url'),
                "permanent_url" :   response.get('data')[0].get('url'),
            }
        }
    elif service == service_name['gemini'] and type == 'video':
        return {
            "data" : {
                "content" : response.get('data')[0].get('text_content'),
                "file_data" : response.get('data')[0].get('file_reference')
            }
        }
    elif service == service_name['openai']:
        image_urls = []
        for image_data in response.get('data', []):
            image_urls.append({
                "revised_prompt": image_data.get('revised_prompt'),
                "image_url": image_data.get('original_url'),
                "permanent_url": image_data.get('url')
            })
        
        return {
            "data": {
                "image_urls": image_urls
            }
        }
    
    elif service == service_name['anthropic']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("content", [{}])[0].get("text", None),
                "model" : response.get("model", None),
                "role" : response.get("role", None),
                "tools_data": tools_data or {},
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("stop_reason", ""))
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
                "tools_data": tools_data or {},
                "fallback" : response.get('fallback') or False,
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None)
            }
        }
    elif service == service_name['open_router']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
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
    elif service == service_name['openai_completion']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
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
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
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
    elif service == service_name['ai_ml']:
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "tools_data": tools_data or {},
                "images" : images,
                "annotations" : response.get("choices", [{}])[0].get("message", {}).get("annotations", None),
                "fallback" : response.get('fallback') or False,
                "firstAttemptError" : response.get('firstAttemptError') or '',
                "finish_reason" : finish_reason_mapping(response.get("choices", [{}])[0].get("finish_reason", ""))
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None),
                "cached_tokens" : response.get("usage", {}).get("prompt_tokens_details",{}).get('cached_tokens')

            }
        }

async def validateResponse(alert_flag, configration, bridgeId, message_id, org_id):
    if alert_flag:
        await send_alert(data={"response":"\n..\n","configration":configration,"message_id":message_id,"bridge_id":bridgeId, "org_id": org_id, "message": "\n issue occurs"})

async def send_alert(data):
    dataTosend = {**data, "ENVIROMENT":Config.ENVIROMENT} if Config.ENVIROMENT else data
    if(data.get("new_configuration", None)):
        await fetch("https://flow.sokt.io/func/scriuEklU2Bu",method='POST',json_body=dataTosend)
    else:
        await fetch("https://flow.sokt.io/func/scriYP8m551q",method='POST',json_body=dataTosend)

def finish_reason_mapping(finish_reason):
    finish_reason_mapping = {
        # Completed / natural stop
        "stop": "completed",        #openai #open_router #gemini
        "end_turn": "completed",    #anthropic
        "completed": "completed",   #openai_response

        # Truncation due to token limits
        "length": "truncated",              #openai #open_router #gemini
        "max_tokens": "truncated",          #anthropic
        "max_output_tokens": "truncated",    #openai_response

        # Tool / function invocation
        "tool_calls": "tool_call",    #openai #gemini
        "tool_use": "tool_call",      #anthropic
    }
    return finish_reason_mapping.get(finish_reason, "other")