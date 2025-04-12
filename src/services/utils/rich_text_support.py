from typing import Any, Dict, Optional
import pydash as _
import uuid
from src.configs.constant import bridge_ids
from .ai_call_util import call_ai_middleware

async def process_chatbot_response(result, params, data, model_config, modelOutputConfig):


    try:
        user_reference = ""
        user_contains = ""
        tool_call_mapping = result.get('historyParams', {}).get('tools_call_data', [])
        avilable_tools = params.get('tools', [])
        if data.get('user_reference'): 
            user_reference = f"\"User reference\": \"{data.get('user_reference')}\""
            user_contains = "On the base of user reference"

        function_calls = []
        if tool_call_mapping:
            for tool in tool_call_mapping:
                for tool_data in tool.values():
                    description = next((tool for tool in avilable_tools if tool.get('name') == tool_data.get('name')), {}).get('description', '')
                    function_calls.append({
                        "id": tool_data.get('id'),
                        "description": description,
                        "input_data": tool_data.get('args'),
                        "response": tool_data.get('response'),
                    })

        random_id = str(uuid.uuid4())

        bridge_id = bridge_ids['chatbot_response_with_actions'] if data.get('actions') else bridge_ids['chatbot_response_without_actions']
        user = f"Generate UI. User message: {data.get('user')}, \n Answer: {_.get(result.get('modelResponse', {}), modelOutputConfig.get('message'))}"
        variables =  { "actions" : data.get('actions') or {}, "user_reference": user_reference, "user_contains": user_contains, "function_calls": function_calls}
        thread_id =  f"{data.get('thread_id') or random_id}-{data.get('sub_thread_id') or random_id}",
        response = await call_ai_middleware(user, bridge_id = bridge_id, varaibles = variables, thread_id = thread_id)
        response['response']['data'] = response.get('response',{}).get('data',{}).get('content',"")
       
        _.set_(result['modelResponse'], modelOutputConfig.get('message'), response['response']['data'])
        result['historyParams']['chatbot_message'] = response['response']['data']
        return
            
    except Exception as err:
        print("Error calling function=>", err)





    # try:
    #     user_reference = ""
    #     user_contains = ""
    #     # validation for the check response
    #     Helper.parse_json(_.get(result.get("modelResponse", {}), modelOutputConfig.get("message")))
    # except Exception as e:
    #     if _.get(result.get("modelResponse", {}), modelOutputConfig.get("tools")):
    #         raise RuntimeError("Function calling has been done 6 times, limit exceeded.")
    #     raise RuntimeError(e)    
    # if params.get('actions'): 
    #     system_prompt = (await ConfigurationService.get_template_by_id(Config.MUI_TEMPLATE_ID)).get('template', '')
    # else: 
    #     system_prompt = (await ConfigurationService.get_template_by_id(Config.MUI_TEMPLATE_ID_WITHOUT_ACTION)).get('template', '')
        
    # if params.get('user_reference'): 
    #     user_reference = f"\"user reference\": \"{params.get('user_reference')}\""
    #     user_contains = "on the base of user reference"
    # params["configuration"]["prompt"], missing_vars = Helper.replace_variables_in_prompt(system_prompt, { "actions" : params.get('actions'), "user_reference": user_reference, "user_contains": user_contains})
    # params["user"] = f"user: {data.get('user')}, \n Answer: {_.get(result.get('modelResponse', {}), modelOutputConfig.get('message'))}"
    # params["template"] = None
    # params['token_calculator']
    # tools = result.get('historyParams', {}).get('tools')
    # if 'customConfig' in params and 'tools' in params['customConfig']:
    #     del params['customConfig']['tools']
    # if params["configuration"].get('conversation'):
    #     del params["configuration"]['conversation']
    # model_response_content = result.get('historyParams', {}).get('message')
    # # custom config for the rich text
    # if data.get('service') != "anthropic":
    #     params['customConfig']['response_type'] = {"type": "json_object"}
    # params['customConfig']['max_tokens'] = model_config['configuration']['max_tokens']['max']
    # if params.get('tools'):
    #     del params['tools']
    # obj = await Helper.create_service_handler(params, data.get('service'))
    # newresult = await obj.execute()
    # newresult['usage'] = params['token_calculator'].calculate_usage(newresult['modelResponse'])
    # _.set_(result['modelResponse'], modelOutputConfig.get('message'), _.get(newresult.get('modelResponse', {}), modelOutputConfig.get('message')))
    # newresult['historyParams']['AiConfig'] =result['historyParams']['AiConfig']
    # newresult['historyParams']['tools_call_data'] = result.get('historyParams', {}).get('tools_call_data')
    # result['historyParams'] = deepcopy(newresult.get('historyParams', {}))
    # result['historyParams']['message'] = model_response_content
    # result['historyParams']['chatbot_message'] = newresult['historyParams']['message']
    # result['historyParams']['user'] = data.get('user')
    # result['historyParams']['tools'] = tools
