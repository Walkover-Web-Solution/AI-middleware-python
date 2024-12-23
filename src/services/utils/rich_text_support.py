
from typing import Any, Dict, Optional
import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from config import Config
import pydash as _
from copy import deepcopy


async def process_chatbot_response(result, params, data, model_config, modelOutputConfig):
    try:
        user_reference = ""
        user_contains = ""
        # validation for the check response
        Helper.parse_json(_.get(result.get("modelResponse", {}), modelOutputConfig.get("message")))
    except Exception as e:
        if _.get(result.get("modelResponse", {}), modelOutputConfig.get("tools")):
            raise RuntimeError("Function calling has been done 6 times, limit exceeded.")
        raise RuntimeError(e)
    
    if params.get('actions'): 
        system_prompt = (await ConfigurationService.get_template_by_id(Config.MUI_TEMPLATE_ID)).get('template', '')
    else: 
        system_prompt = (await ConfigurationService.get_template_by_id(Config.MUI_TEMPLATE_ID_WITHOUT_ACTION)).get('template', '')
        
    if params.get('user_reference'): 
        user_reference = f"\"user reference\": \"{params.get('user_reference')}\""
        user_contains = "on the base of user reference"
    params["configuration"]["prompt"], missing_vars = Helper.replace_variables_in_prompt(system_prompt, { "actions" : params.get('actions'), "user_reference": user_reference, "user_contains": user_contains})
    params["user"] = f"user: {data.get('user')}, \n Answer: {_.get(result.get('modelResponse', {}), modelOutputConfig.get('message'))}"
    params["template"] = None
    tools = result.get('historyParams', {}).get('tools')
    if 'customConfig' in params and 'tools' in params['customConfig']:
        del params['customConfig']['tools']
    if params["configuration"].get('conversation'):
        del params["configuration"]['conversation']
    model_response_content = result.get('historyParams', {}).get('message')
    # custom config for the rich text
    if data.get('service') != "anthropic":
        params['customConfig']['response_type'] = {"type": "json_object"}
    params['customConfig']['max_tokens'] = model_config['configuration']['max_tokens']['max']
    if params.get('tools'):
        del params['tools']
    obj = await Helper.create_service_handler(params, data.get('service'))
    newresult = await obj.execute()
    tokens = obj.calculate_usage(newresult.get("modelResponse", {}))
    if data.get('service') == "anthropic":
        _.set_(result['usage'], "totalTokens", _.get(result['usage'], "totalTokens") + tokens['totalTokens'])
        _.set_(result['usage'], "inputTokens", _.get(result['usage'], "inputTokens") + tokens['inputTokens'])
        _.set_(result['usage'], "outputTokens", _.get(result['usage'], "outputTokens") + tokens['outputTokens'])
    elif data.get('service') == 'openai' or data.get('service') == 'groq':
        _.set_(result['usage'], "totalTokens", _.get(result['usage'], "totalTokens") + tokens['totalTokens'])
        _.set_(result['usage'], "inputTokens", _.get(result['usage'], "inputTokens") + tokens['inputTokens'])
        _.set_(result['usage'], "outputTokens", _.get(result['usage'], "outputTokens") + tokens['outputTokens'])
        _.set_(result['usage'], "expectedCost", _.get(result['usage'], "expectedCost") + tokens['expectedCost'])
    _.set_(result['modelResponse'], modelOutputConfig.get('message'), _.get(newresult.get('modelResponse', {}), modelOutputConfig.get('message')))
    newresult['historyParams']['tools_call_data'] = result.get('historyParams', {}).get('tools_call_data')
    result['historyParams'] = deepcopy(newresult.get('historyParams', {}))
    result['historyParams']['message'] = model_response_content
    result['historyParams']['chatbot_message'] = newresult['historyParams']['message']
    result['historyParams']['user'] = data.get('user')
    result['historyParams']['tools'] = tools