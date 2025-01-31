import pydash as _
import re
import httpx
import asyncio
import json 
from src.configs.constant import service_name
import pydash as _
from src.services.utils.apiservice import fetch
from fastapi import Request
import datetime

def validate_tool_call(modelOutputConfig, service, response):
    match service:
        case 'openai' | 'groq':
            return len(response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0
        case 'anthropic':
            return response.get('stop_reason') == 'tool_use'
        case _:
            return False

async def axios_work(data, function_name):
    try:    
        response,rs_headers = await fetch(f"https://flow.sokt.io/func/{function_name}","POST",None,None,data) # required is not send then it will still hit the curl
        return {
            'response': response,
            'metadata':{
                'flowHitId': rs_headers.get('flowHitId'),
            },
            'status': 1
        }
        
    except Exception as err:
        print("Error calling function=>",function_name,  err)
        return {
            'response': str(err),
            'metadata':{
                'error': str(err),
            },
            'status': 0
        }

# [?] won't work for the case addess.name[0]
def get_nested_value(dictionary, key_path):
    keys = key_path.split('.')
    for key in keys:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return None
    return dictionary

# https://docs.google.com/document/d/1WkXnaeAhTUdAfo62SQL0WASoLw-wB9RD9N-IeUXw49Y/edit?tab=t.0 => to see the variables example
def transform_required_params_to_required(properties, variables={}, variables_path={}, function_name=None, parent_key=None, parentValue=None):
    if not isinstance(properties, dict):
        return properties
    transformed_properties = properties.copy()
    for key, value in properties.items():
        if value.get('required_params') is not None:
            transformed_properties[key]['required'] = value.pop('required_params')
        key_to_find = f"{parent_key}.{key}" if parent_key else key
        if variables_path is not None and variables_path.get(function_name) and key_to_find in variables_path[function_name]:
            variable_path_value = variables_path[function_name][key_to_find]
            if_variable_has_value = get_nested_value(variables, variable_path_value)
            if if_variable_has_value:
                del transformed_properties[key]
                if parentValue and 'required' in parentValue and key in parentValue['required']:
                    parentValue['required'].remove(key)
                continue
        for prop_key in ['parameter', 'properties']:
            if prop_key in value:
                transformed_properties[key]['properties'] = transform_required_params_to_required(value.pop(prop_key), variables, variables_path, function_name, key, value)
                break
        else:
            items = value.get('items', {})
            item_type = items.get('type')
            if item_type == 'object':
                nextedObject = {'properties': transform_required_params_to_required( items.get('properties', {}), variables, variables_path, function_name, key, value)}
                nextedObject = {**nextedObject, "required": items.get('required', []), "type": item_type}
                transformed_properties[key]['items'] = nextedObject
            elif item_type == 'array':
                transformed_properties[key]['items'] = transform_required_params_to_required( items.get('items', {}), variables, variables_path, function_name, key, value)
    return transformed_properties

def tool_call_formatter(configuration: dict, service: str, variables: dict, variables_path: dict) -> dict:
    if service == service_name['openai']:
        data_to_send =  [
            {
                'type': 'function',
                'function': {
                    'name': transformed_tool['name'],
                    # "strict": True,
                    'description': transformed_tool['description'],
                    'parameters': {
                        'type': 'object',
                        'properties': transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])}),
                        'required': transformed_tool.get('required', []),
                        # "additionalProperties": False,
                    }
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
        return data_to_send
    elif service == service_name['anthropic']:
        return  [
            {
                'name': transformed_tool['name'],
                'description': transformed_tool['description'],
                'input_schema': {
                    "type": "object",
                    'properties': transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])}),
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
                    "properties": transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])}),
                    "required": transformed_tool.get('required', []),
                },
                    },
            } for transformed_tool in configuration.get('tools', [])
        ]

async def send_request(url, data, method, headers):
    try:
        return await fetch(url,method,headers,None, data)
    except Exception as e:
        print('Unexpected error:',url, e)
        return {'error': 'Unexpected error', 'details': str(e)}
    
async def send_message(cred, data ):
    try:
        response = await fetch(
            f"https://api.rtlayer.com/message?apiKey={cred['apikey']}","POST",None,None,
            {
                **cred,
                'message': json.dumps(data)
            }
        )
        return response
    except httpx.RequestError as error:
        print('send message error=>', error)
    except Exception as e:
        print('Unexpected error=>', e)


async def sendResponse(response_format, data, success = False, variables={}):
    data_to_send = {
        'response' if success else 'error': data,
        'success': success
    }
    try:
        match response_format['type']:
            case 'RTLayer' : 
                return await send_message(cred = response_format['cred'], data=data_to_send)
            case 'webhook':
                data_to_send['variables'] = variables
                return await send_request(**response_format['cred'], method='POST', data=data_to_send)
    except Exception as e:
        print("error sending request", e)

async def process_data_and_run_tools(codes_mapping, names, tool_id_and_name_mapping):
    try:
        responses = []
        tool_call_logs = {**codes_mapping} 

        # Prepare tasks for async execution
        tasks = []

        for tool_call_key, tool in codes_mapping.items():
            name = tool['name']

            # Get corresponding function code mapping
            tool_mapping = {} if tool_id_and_name_mapping[name] in names else {"error": True, "response": "Wrong Function name"}
            tool_data = {**tool, **tool_mapping}

            if not tool_data.get("response"):
                # if function is present in db/NO response, create task for async processing
                task = axios_work(tool_data.get("args"), tool_id_and_name_mapping[name])
                tasks.append((tool_call_key, tool_data, task))
            else:
                # If function is not present in db/response exists, append to responses
                responses.append({
                    'tool_call_id': tool_call_key,
                    'role': 'tool',
                    'name': tool['name'],
                    'content': json.dumps(tool_data['response'])
                })
                # Update tool_call_logs with existing response
                tool_call_logs[tool_call_key] = {**tool, "response": tool_data['response']}

        # Execute all tasks concurrently if any exist
        if tasks:
            task_results = await asyncio.gather(
                *[task[2] for task in tasks], return_exceptions=True
            ) # return_exceptions use for the handle the error occurs from the task

            # Process each result
            for i, (tool_call_key, tool_data, _) in enumerate(tasks):
                result = task_results[i]

                # Handle any exceptions or errors
                if isinstance(result, Exception):
                    response = {"error": "Error during async task execution", "details": str(result)}
                elif tool_data.get('error'):
                    response = {"error":"Args / Input is not proper JSON"}
                else:
                    response = result

                # Append formatted response
                responses.append({
                    'tool_call_id': tool_call_key,  # Replacing with tool_call_key
                    'role': 'tool',
                    'name': tool_data['name'],
                    'content': json.dumps(response)
                })

                # Update tool_call_logs with the response
                tool_call_logs[tool_call_key] = {**tool_data, **response}

        # Create mapping by tool_call_id (now tool_call_key) for return
        mapping = {resp['tool_call_id']: resp for resp in responses}

        return responses, mapping, tool_call_logs

    except Exception as error:
        print(f"Error in process_data_and_run_tools: {error}")
        raise error
  


def make_code_mapping_by_service(responses, service):
    codes_mapping = {}
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
                    'name': name,
                    'args': args,
                    "error": error
                }
        case 'anthropic':
            for tool_call in responses['content'][1:]:  # Skip the first item
                name = tool_call['name']
                args = tool_call['input']
                codes_mapping[tool_call["id"]] = {
                    'name': name,
                    'args': args,
                    "error": False
                }
        case _:
            return False, {}
    return codes_mapping
    
def convert_datetime(obj):
    """Recursively convert datetime objects in a dictionary or list to ISO format strings."""
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(item) for item in obj]
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()  # Convert datetime to ISO format string
    else:
        return obj

async def make_request_data(request: Request):
    body = await request.json()
    state_data = {}
    path_params = {}
    
    attributes = ['is_playground', 'version', 'profile']
    for attr in attributes:
        if hasattr(request.state, attr):
            state_data[attr] = getattr(request.state, attr)
    
    if hasattr(request.state, 'timer'):
        state_data['timer'] = request.state.timer
        
    if hasattr(request, 'path_params'):
        path_params = request.path_params
        
    body = convert_datetime(body)
    state_data = convert_datetime(state_data)
        
    result = {
        'body': body,
        'state': state_data,
        'path_params': path_params
    }
    return result