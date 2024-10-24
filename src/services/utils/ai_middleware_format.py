from src.services.utils.apiservice import fetch
async def  Response_formatter(response, service):
    if service == 'openai':
        return {
            "data" : {
                "id" : response.get("id", None),
                "content" : response.get("choices", [{}])[0].get("message", {}).get("content", None),
                "model" : response.get("model", None),
                "role" : response.get("choices", [{}])[0].get("message", {}).get("role", None),
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None)
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
                "finish_reason" : response.get("stop_reason", None)
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
                "finish_reason" : response.get("choices", [{}])[0].get("finish_reason", None)
            },
            "usage" : {
                "input_tokens" : response.get("usage", {}).get("prompt_tokens", None),
                "output_tokens" : response.get("usage", {}).get("completion_tokens", None),
                "total_tokens" : response.get("usage", {}).get("total_tokens", None)
            }
        }

async def validateResponse(final_response,configration,bridgeId):
    parsed_data = final_response.get("data",{}).get("content","").replace(" ", "").replace("\n", "")
    if(parsed_data == ''):
        await send_alert(data={"final_response":final_response,"configration":configration,"bridgeId":bridgeId})

async def send_alert(data):
    await fetch("https://flow.sokt.io/func/scriYP8m551q",method='POST',json_body=data)