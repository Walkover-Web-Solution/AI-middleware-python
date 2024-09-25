import pydash as _
import re
import requests
import httpx
import json 
from src.configs.constant import service_name

def validate_tool_call(modelOutputConfig, service, response):
    match service:
        case 'openai' | 'groq':
            return len(response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0
        case 'anthropic':
            return response.get('stop_reason') == 'tool_use'
        case _:
            return False

async def axios_work_js(data, axios_function):
    try:    
        pattern = r"https?:\/\/(flow\.sokt\.io|prod-flow-vm\.viasocket\.com)\/func\/([a-zA-Z0-9]+)"
        match = re.search(pattern, axios_function)
        script_id = match.group(2)
        response = requests.post(f"https://flow.sokt.io/func/{script_id}", json=data)
        return {
            'response': response.json(),
            'metadata':{
                'flowHitId': response.headers.get('flowHitId'),
            },
            'status': 1
        }
        
    except Exception as err:
        print("Error calling function=>", err)
        return {
            'response': str(err),
            'metadata':{
                'error': str(err),
            },
            'status': 0
        }
    
async def axios_work(data, code, is_python=False):
    try:
        if not is_python:
            return await axios_work_js(data, code)
        
        # Append the execution code to the provided code
        exec_code = code + """
result = axios_call(params)
headers = {} 
if isinstance(result, tuple) and len(result) == 2:
    result, headers = result
"""
        # Prepare the environment for execution
        local_vars = {'params': data}
        global_vars = {"requests": requests, "asyncio": __import__('asyncio')}

        exec(exec_code, global_vars, local_vars)
        return {
            'response': local_vars.get('result'),
            'metadata':{
                'flowHitId': local_vars.get('headers').get('flowHitId'),
            },
            'status': 1
        }
    except Exception as err:
        return {
            'response': str(err),
            'metadata':{
                'error': str(err),
            },
            'status': 0
        }
    

def tool_call_formatter(configuration: dict, service: str) -> dict:
    if service == service_name['openai']:
        return  [
            {
                'type': 'function',
                'function': {
                    'name': transformed_tool['name'],
                    'description': transformed_tool['description'],
                    'parameters': {
                        'type': 'object',
                        'properties': transformed_tool.get('properties', {}),
                        'required': transformed_tool.get('required', [])
                    }
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
    elif service == service_name['anthropic']:
        return  [
            {
                'name': transformed_tool['name'],
                'description': transformed_tool['description'],
                'input_schema': {
                    "type": "object",
                    'properties': transformed_tool.get('properties', {}),
                    'required': transformed_tool.get('required', [])
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
    elif service == service_name['groq']:
        return [
            {
            "type": "function",
            "function": {
                "name": transformed_tool['name'],
                "description": transformed_tool['description'],
                "parameters": {
                    "type": "object",
                    "properties": transformed_tool.get('properties', {}),
                    "required": transformed_tool.get('required', []),
                },
                    },
            } for transformed_tool in configuration.get('tools', [])
        ]


async def send_request(url, data, method, headers):
    try:
        response = requests.request(method, url, json=json.dumps(data), headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print('Unexpected error:', e)
        return {'error': 'Unexpected error', 'details': str(e)}
    
async def send_message(cred, data ):
    try:
        response = requests.post(
            url=f"https://api.rtlayer.com/message?apiKey={cred['apikey']}",
            data={
                **cred,
                'message': json.dumps(data)
            }
        )
        return response
    except httpx.RequestError as error:
        print('send message error=>', error)
    except Exception as e:
        print('Unexpected error=>', e)


async def sendResponse(response_format, data, success = False):
    data_to_send = {
        'response' if success else 'error': data,
        'success': success
    }
    try:
        match response_format['type']:
            case 'RTLayer' : 
                return await send_message(cred = response_format['cred'], data=data_to_send)
            case 'webhook':
                return await send_request(**response_format['cred'], method='POST', data=data_to_send)
    except Exception as e:
        print("error sending request", e)

async def process_data_and_run_tools(codes_mapping, function_code_mapping):

    async def process_code_and_service_data(api_call):
            axios_instance = api_call.get('code')
            is_python = api_call.get('is_python')
            args= api_call.get("args")
            api_response = await axios_work(args, axios_instance, is_python)
            return api_response

    try:
        responses = []
        mapping = {}

        # Iterate through each tool and process the API calls in one loop
        for tool in codes_mapping.values():
            tool_call_id = tool["tool_call"]["id"]
            name = tool['name']
            
            # Get the function code mapping for the current tool
            tool_mapping = function_code_mapping.get(name, {"error": True, "response": "Wrong Function name"})
            
            # Combine tool data with function code mapping
            tool_data = {**tool, **tool_mapping}

            # Process the API call if no response exists
            if not tool_data.get("response"):
                api_response = await process_code_and_service_data(tool_data)
                response = api_response if not tool_data.get('error') else "Args / Input is not proper JSON"
            else:
                response = tool_data.get("response")

            # Store the response
            tool_data['response'] = response

            # Format the data to be returned
            formatted_data = {
                'tool_call_id': tool_call_id, 
                'role': 'tool', 
                'name': tool_data['name'], 
                'content': json.dumps(response)
            }

            # Append to responses and mapping
            responses.append(formatted_data)
            mapping[tool_call_id] = formatted_data

        return responses, mapping

    except Exception as error:
        print(f"Error in createMapping: {error}")
        raise error
    


def make_code_mapping_by_service(responses, service):
    codes_mapping = {}
    names = []
    match service:
        case 'openai' | 'groq':
            for tool_call in responses['choices'][0]['message']['tool_calls']:
                name = tool_call['function']['name']
                error = False
                try:
                    args = json.loads(tool_call['function']['arguments'])
                except json.JSONDecodeError:
                    args = {
                        "error": tool_call['function']['arguments']
                    }
                    error = True
                codes_mapping[tool_call["id"]] = {
                    'tool_call': tool_call,
                    'name': name,
                    'args': args,
                    "error": error
                }
                names.append(name)
        case 'anthropic':
            for tool_call in responses['content'][1:]:  # Skip the first item
                name = tool_call['name']
                args = tool_call['input']
                codes_mapping[tool_call["id"]] = {
                    'tool_call': tool_call,
                    'name': name,
                    'args': args,
                    "error": False
                }
                names.append(name)
        case _:
            return False, {}
    return codes_mapping, names