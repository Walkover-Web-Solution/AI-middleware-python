import pydash as _
import re
import requests
import httpx
import json 
from src.configs.constant import service_name

def validate_tool_call(modelOutputConfig, service, response):
    match service:
        case 'openai' | 'groq':
            return bool(_.get(response, modelOutputConfig.get('tools')))
        case 'anthropic':
            return response.get('stop_reason') == 'tool_use'
        case _:
            return False

async def fetch_axios(ConfigurationService, name):
    api_call = await ConfigurationService.get_api_call_by_name(name)
    axios_instance = api_call['apiCall'].get('code') or api_call['apiCall'].get('axios')  
    is_python = api_call['apiCall'].get('is_python', False)
    return axios_instance, is_python

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
            'response': '',
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
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, json=data, headers=headers)
            return response
    except httpx.RequestError as error:
        print("send_request error=>", error)
        return None
    
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