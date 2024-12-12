import json
from config import Config
from src.services.utils.apiservice import fetch

async def Response_formatter(response, service, tools={}, type='chat'):
    tools_data = tools
    if isinstance(tools_data, dict):
                for key, value in tools_data.items():
                    if isinstance(value, str):
                        try:
                            tools_data[key] = json.loads(value)
                        except json.JSONDecodeError:
                            pass
                        
    if service == 'openai' and type =='chat' :
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
    elif service == 'openai' and type =='image' :
        return {
            "data" : {
                "revised_prompt" : response.get('data')[0].get('revised_prompt'),
                "image_url" : response.get('data')[0].get('url')
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

async def validateResponse(final_response,configration,bridgeId, message_id, org_id):
    content = final_response.get("data",{}).get("content","")
    parsed_data = content.replace(" ", "").replace("\n", "")
    if(parsed_data == '' and content):
        await send_alert(data={"response":content,"configration":configration,"message_id":message_id,"bridge_id":bridgeId, "org_id": org_id, "message": "\n issue occurs"})

async def send_alert(data):
    dataTosend = {**data, "ENVIROMENT":Config.ENVIROMENT} if Config.ENVIROMENT else data
    await fetch("https://flow.sokt.io/func/scriYP8m551q",method='POST',json_body=dataTosend)