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
from src.controllers.rag_controller import get_text_from_vectorsQuery
from globals import *
from src.db_services.ConfigurationServices import get_bridges_without_tools, update_bridge
from src.services.utils.ai_call_util import call_gtwy_agent
from globals import *

def clean_json(data):
    """Recursively remove keys with empty string, empty list, or empty dictionary."""
    if isinstance(data, dict):
        return {k: clean_json(v) for k, v in data.items() if v not in ['', []]}
    elif isinstance(data, list):
        return [clean_json(item) for item in data]
    else:
        return data

def validate_tool_call(service, response):
    match service: # TODO: Fix validation process.
        case 'openai' | 'groq' | 'open_router':
            return len(response.get('choices', [])[0].get('message', {}).get("tool_calls", [])) > 0
        case 'openai_response':
            return response.get('output')[0]['type'] == 'function_call'
        case 'anthropic':
            for item in response.get('content', []):
                if item.get('name') == 'JSON_Schema_Response_Format':
                    response['content'][0]['text'] = json.dumps(item.get('input'))
                    return False
            return response.get('stop_reason') == 'tool_use'
        case _:
            return False

async def axios_work(data, function_payload):
    try:    
        response,rs_headers = await fetch(function_payload.get("url"),"POST",function_payload.get("headers",{}),None,data) # required is not send then it will still hit the curl
        return {
            'response': response,
            'metadata':{
                'flowHitId': rs_headers.get('flowHitId'),
            },
            'status': 1
        }
        
    except Exception as err:
        logger.error("Error calling function axios_work => ",function_payload.get("url"),  err)
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
    if properties.get('type') == 'array' or properties.get('type') == 'object':
        return {'items':properties}
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
                transformed_properties[key]['items']['type'] = 'array'
    return transformed_properties

def tool_call_formatter(configuration: dict, service: str, variables: dict, variables_path: dict) -> dict:
    if service == service_name['openai'] or service == service_name['open_router']:
        data_to_send =  [
            {
                'type': 'function',
                'function': {
                    'name': transformed_tool['name'],
                    # "strict": True,
                    'description': transformed_tool['description'],
                    'parameters': {
                        'type': 'object',
                        'properties': clean_json(transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])})),
                        'required': transformed_tool.get('required'),
                        # "additionalProperties": False,
                    }
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
        return data_to_send
    elif service == service_name['openai_response']:
        data_to_send =  [
            {
                'type': 'function',
                'name': transformed_tool['name'],
                # "strict": True,
                'description': transformed_tool['description'],
                'parameters': {
                    'type': 'object',
                    'properties': clean_json(transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])})),
                    'required': transformed_tool.get('required'),
                    # "additionalProperties": False,
                }
            } for transformed_tool in configuration.get('tools', [])
        ]
        return data_to_send
    elif service == service_name['anthropic']:
        return [
            transformed_tool if transformed_tool['name'] == 'JSON_Schema_Response_Format' else {
                'name': transformed_tool['name'],
                'description': transformed_tool['description'],
                'input_schema': {
                    "type": "object",
                    'properties': clean_json(transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])})),
                    'required': transformed_tool.get('required')
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
                    "properties": clean_json(transform_required_params_to_required(transformed_tool.get('properties', {}), variables=variables, variables_path=variables_path, function_name=transformed_tool['name'], parentValue={'required': transformed_tool.get('required', [])})),
                    "required": transformed_tool.get('required'),
                },
                    },
            } for transformed_tool in configuration.get('tools', [])
        ]

async def send_request(url, data, method, headers):
    try:
        return await fetch(url,method,headers,None, data)
    except Exception as e:
        logger.error(f'Unexpected error:, {url}, {str(e)}')
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
        logger.error(f'send message error=>, {str(error)}')
    except Exception as e:
        logger.error(f'Unexpected send message error=>, {str(e)}')


async def sendResponse(response_format, data, success = False, variables={}):
    data_to_send = {
        'response' if success else 'error': data,
        'success': success
    }
    match response_format['type']:
        case 'RTLayer' : 
            return await send_message(cred = response_format['cred'], data=data_to_send)
        case 'webhook':
            data_to_send['variables'] = variables
            return await send_request(**response_format['cred'], method='POST', data=data_to_send)

async def process_data_and_run_tools(codes_mapping, tool_id_and_name_mapping, org_id, timer, function_time_logs):
    try:
        timer.start()
        executed_functions = []
        responses = []
        tool_call_logs = {**codes_mapping} 

        # Prepare tasks for async execution
        tasks = []
        for tool_call_key, tool in codes_mapping.items():
            name = tool['name']

            # Get corresponding function code mapping
            tool_mapping = {} if tool_id_and_name_mapping[name] else {"error": True, "response": "Wrong Function name"}
            tool_data = {**tool, **tool_mapping}

            if not tool_data.get("response"):
                # if function is present in db/NO response, create task for async processing
                if tool_id_and_name_mapping[name].get('type') == 'RAG':
                    task = get_text_from_vectorsQuery({**tool_data.get("args"), "org_id":org_id}) 
                elif tool_id_and_name_mapping[name].get('type') == 'AGENT':
                    task = call_gtwy_agent({**tool_data.get("args"), "org_id":org_id, "bridge_id": tool_id_and_name_mapping[name].get("bridge_id")})
                else: 
                    task = axios_work(tool_data.get("args"), tool_id_and_name_mapping[name])
                tasks.append((tool_call_key, tool_data, task))
                executed_functions.append(name)
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
                tool_call_logs[tool_call_key] = {**tool_data, **response, "id": tool_id_and_name_mapping[tool_data['name']].get("name")}

        # Create mapping by tool_call_id (now tool_call_key) for return
        mapping = {resp['tool_call_id']: resp for resp in responses}

        # Record executed function names and timing
        executed_names = ", ".join(executed_functions) if executed_functions else "No functions executed"
        function_time_logs.append({"step": executed_names, "time_taken": timer.stop("process_data_and_run_tools")})

        return responses, mapping, tool_call_logs

    except Exception as error:
        print(f"Error in process_data_and_run_tools: {error}")
        traceback.print_exc()
        raise error
  


def make_code_mapping_by_service(responses, service):
    codes_mapping = {}
    function_list = []
    match service:
        case 'openai' | 'groq' | 'open_router':

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
                function_list.append(name)
        case 'openai_response':

            for tool_call in responses['output']:
                name = tool_call['name']
                error = False
                try:
                    args = json.loads(tool_call['arguments'])
                except json.JSONDecodeError:
                    args = {
                        "error": tool_call['arguments']
                    }
                    error = True
                codes_mapping[tool_call["id"]] = {
                    'name': name,
                    'args': args,
                    "error": error
                }
                function_list.append(name)
        case 'anthropic':
            for tool_call in [item for item in responses['content'] if item['type'] == 'tool_use']:  # Skip the first item
                name = tool_call['name']
                args = tool_call['input']
                codes_mapping[tool_call["id"]] = {
                    'name': name,
                    'args': args,
                    "error": False
                }
                function_list.append(name)
        case _:
            return {}, []
    return codes_mapping, function_list
    
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

async def make_request_data_and_publish_sub_queue(parsed_data, result, params, thread_info):
    suggestion_content = {'data': {'content': {}}}
    suggestion_content['data']['content'] = result['historyParams']['message'] if parsed_data['is_rich_text'] == True else result['modelResponse']
    data = {
        "save_sub_thread_id_and_name" : {
            "org_id" : parsed_data['org_id'],
            "thread_id" : thread_info['thread_id'],
            "sub_thread_id" : thread_info['sub_thread_id'],
            "thread_flag" : parsed_data['thread_flag'],
            "response_format" : parsed_data['response_format'],
            "bridge_id" : parsed_data['bridge_id'],
            "user" : parsed_data['user']

        },
        "metrics_service": {
            "dataset": [parsed_data['usage']],
            "history_params": result["historyParams"],
            "version_id": parsed_data['version_id']
        },
        "validateResponse": {
            "final_response": result['modelResponse'],
            "configration": parsed_data['configuration'],
            "bridgeId": parsed_data['bridge_id'],
            "message_id": parsed_data['message_id'],
            "org_id": parsed_data['org_id']
        },
        "total_token_calculation": {
            "tokens": parsed_data['tokens'],
            "bridge_id": parsed_data['bridge_id']
        },
        "get_bridge_avg_response_time": {
            "org_id": parsed_data['org_id'],
            "bridge_id": parsed_data['bridge_id']
        },
        "chatbot_suggestions" : {
            "response_format": parsed_data['response_format'],
            "assistant": suggestion_content,
            "user": parsed_data['user'],
            "bridge_summary": parsed_data['bridge_summary'],
            "thread_id": parsed_data['thread_id'],
            "sub_thread_id": parsed_data['sub_thread_id'],
            "configuration": params['configuration']
        },
        "handle_gpt_memory" : {
            "id" : parsed_data['id'],
            "user" :  parsed_data['user'],
            "assistant" :  result['modelResponse'],
            "purpose" :  parsed_data['memory'],
            "gpt_memory_context" :  parsed_data['gpt_memory_context']
        },
        "check_handle_gpt_memory" : {
            "gpt_memory" :  parsed_data['gpt_memory'],
            "type" :  parsed_data['configuration']['type']
        },
        "check_chatbot_suggestions" : {
            "bridgeType" :  parsed_data['bridgeType'],
            }
    }

    return data


def makeFunctionName(name):
    return re.sub(r'[^a-zA-Z0-9_-]', '', name)

async def total_token_calculation(tokens, bridge_id):
    total_tokens = tokens.get('inputTokens', 0) + tokens.get('outputTokens', 0)
    bridge_data = (await get_bridges_without_tools(bridge_id, org_id=None)).get("bridges")
    if bridge_data and 'total_tokens' in bridge_data:
        total_tokens = bridge_data['total_tokens'] + total_tokens
    else:
        total_tokens = total_tokens
    
    # Fix: update_bridge expects update_fields as a dictionary parameter
    await update_bridge(bridge_id=bridge_id, update_fields={'total_tokens': total_tokens})