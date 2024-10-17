import pydash as _
import re
import requests
import httpx
import json 
from src.configs.constant import service_name
import pydash as _
import requests

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
        response = requests.post(f"https://flow.sokt.io/func/{function_name}", json=data) # required is not send then it will still hit the curl
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
        if variables_path.get(function_name) and key_to_find in variables_path[function_name]:
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
                transformed_properties[key]['items'] = transform_required_params_to_required( items.get('properties', {}), variables, variables_path, function_name, key, value)
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

    async def process_code_and_service_data(api_call, function_name):
            args= api_call.get("args")
            api_response = await axios_work(args, function_name)
            return api_response

    try:
        responses = []
        mapping = {}
        replica_code_mapping = {**codes_mapping}

        # Iterate through each tool and process the API calls in one loop
        for tool_call_key, tool in codes_mapping.items():
            tool_call_id = tool["tool_call"]["id"]
            name = tool['name']
            
            # Get the function code mapping for the current tool
            tool_mapping = function_code_mapping.get(name, {"error": True, "response": "Wrong Function name"})
            
            # Combine tool data with function code mapping
            tool_data = {**tool, **tool_mapping}

            # Process the API call if no response exists
            if not tool_data.get("response"):
                api_response = await process_code_and_service_data(tool_data, function_name=name)
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
            replica_code_mapping[tool_call_key] = {
                **replica_code_mapping[tool_call_key],
                **response
            }

            # Append to responses and mapping
            responses.append(formatted_data)
            mapping[tool_call_id] = formatted_data
        return responses, mapping, replica_code_mapping

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