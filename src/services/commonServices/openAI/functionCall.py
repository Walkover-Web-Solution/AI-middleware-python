import asyncio
import json
import logging
from .chat import chats
from ....db_services import ConfigurationServices as ConfigurationService
import requests
from ...utils.customRes import ResponseSender


async def function_call(data):
    try:
        configuration = data.get('configuration')
        apikey = data.get('apikey')
        bridge = data.get('bridge')
        tools_call = data.get('tools_call')
        output_config = data.get('outputConfig')
        l = data.get('l', 0)
        rtl_layer = data.get('rtlLayer', False)
        body = data.get('body', {})
        playground = data.get('playground', False)
        tools = data.get('tools', {})
        api_endpoints =  set(bridge.get('api_endpoints', []))
        api_name = tools_call.get('function', {}).get('name')

        if api_name in api_endpoints:
            api_info = bridge['api_call'][api_name]
            axios_instance = await fetch_axios(api_info)
            args = json.loads(tools_call['function'].get('arguments', '{}'))
            api_response = await axios_work(args, axios_instance)
            print(api_response, 'api response')
            func_response_data = {
                'tool_call_id': tools_call['id'],
                'role': 'tool',
                'name': api_name,
                'content': json.dumps(api_response),
            }
            tools[api_name] = json.dumps(api_response)
            configuration['messages'].append({'role': 'assistant', 'content': None, 'tool_calls': [tools_call]})
            configuration['messages'].append(func_response_data)

            if not playground:
                ResponseSender.sendResponse({
                    'rtlLayer': rtl_layer,
                    'data': {'function_call': False, 'success': True, 'message': 'Going to GPT'},
                    'reqBody': body,
                    'headers': {}
                })

            open_ai_response = await chats(configuration, apikey)
            model_response = open_ai_response.get('modelResponse', {})
            open_ai_response['tools'] = tools

            if not open_ai_response.get('success'):
                return {'success': False, 'error': open_ai_response.get('error')}

            if model_response.get(output_config['tools']) and l <= 3:
                if not playground:
                    ResponseSender.sendResponse({
                        'rtlLayer': rtl_layer,
                        'data': {'function_call': True, 'success': True, 'message': 'sending the next function call'},
                        'reqBody': body,
                        'headers': {}
                    })

                data['l'] = data['l'] + 1
                data['tools_call'] = model_response[output_config['tools']][0]
                data['tools'] = tools
                return await function_call(data)

            return open_ai_response

        return {'success': False, 'error': 'endpoint does not exist'}

    except Exception as error:
        logging.error("function call error:", exc_info=error)
        return {'success': False, 'error': str(error)}

async def fetch_axios(api_info):
    api_call = await ConfigurationService.get_api_call_by_id(api_info['apiObjectID'])
    return api_call['apiCall']['axios']

async def axios_work(data, axios_function):
    # create_function = eval(f"lambda axios, data: {axios_function}")
    exec_globals = {}
    exec(axios_function, exec_globals)
    
    # Access the send_data function from the exec_globals dictionary
    send_data = exec_globals.get('send_data')
    print('send_data', send_data)
    try:
        response = send_data(data)
        return response.json()
    except Exception as err:
        logging.error("error", exc_info=err)
        return {'success': False}

# Exporting function_call function
__all__ = ["function_call"]
