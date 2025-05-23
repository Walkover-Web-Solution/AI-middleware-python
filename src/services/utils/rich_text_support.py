from typing import Any, Dict, Optional
import pydash as _
import uuid
from src.configs.constant import bridge_ids
from .ai_call_util import call_ai_middleware
import json
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
        if(data.get('actions')): user += "If the component action type is reply then choose the button action type reply else choose it sendDatatoFrontend"
        variables =  { "actions" : data.get('actions') or {}, "user_reference": user_reference, "user_contains": user_contains, "function_calls": function_calls}
        thread_id =  f"{data.get('thread_id') or random_id}-{data.get('sub_thread_id') or random_id}"
        response = await call_ai_middleware(user, bridge_id = bridge_id, variables = variables, thread_id = thread_id)
        response = json.dumps(response)
        _.set_(result['modelResponse'], modelOutputConfig.get('message'), response)
        result['historyParams']['chatbot_message'] = response
        return
            
    except Exception as err:
        print("Error calling function=>", err)
