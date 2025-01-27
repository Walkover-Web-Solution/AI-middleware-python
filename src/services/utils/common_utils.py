from fastapi import APIRouter, Request
import uuid
from typing import Any, Dict, Optional
from src.services.utils.time import Timer
from src.configs.modelConfiguration import ModelsConfig
from src.services.commonServices.baseService.utils import axios_work
from src.services.utils.apiservice import fetch
from src.configs.serviceKeys import model_config_change
from ...controllers.conversationController import getThread
from src.services.utils.token_calculation import TokenCalculator
import src.db_services.ConfigurationServices as ConfigurationService
from .helper import Helper
from config import Config
import pydash as _
import asyncio
from ..commonServices.baseService.utils import sendResponse
from ...db_services import metrics_service as metrics_service
from ..utils.ai_middleware_format import validateResponse
from ..utils.gpt_memory import handle_gpt_memory
from datetime import datetime

def parse_request_body(request_body):
    body = request_body.get('body', {})
    state = request_body.get('state', {})
    path_params = request_body.get('path_params', {})
    
    return {
        "body": body,
        "state": state,
        "path_params": path_params,
        "apikey": body.get("apikey"),
        "bridge_id": path_params.get('bridge_id') or body.get("bridge_id"),
        "configuration": body.get("configuration", {}),
        "thread_id": body.get("thread_id"),
        "sub_thread_id": body.get('sub_thread_id') or body.get("thread_id"),
        "org_id": state.get('profile', {}).get('org', {}).get('id', ''),
        "user": body.get("user"),
        "tools": body.get("configuration", {}).get('tools'),
        "service": body.get("service"),
        "variables": body.get("variables") or {},
        "bridgeType": body.get('chatbot'),
        "template": body.get('template'),
        "response_format": body.get("configuration", {}).get("response_format"),
        "response_type": body.get("configuration", {}).get("response_type"),
        "model": body.get("configuration", {}).get('model'),
        "is_playground": state.get('is_playground', False),
        "bridge": body.get('bridge'),
        "pre_tools": body.get('pre_tools'),
        "version": state.get('version'),
        "fine_tune_model": body.get("configuration", {}).get('fine_tune_model', {}).get('current_model', {}),
        "is_rich_text": body.get("configuration", {}).get('is_rich_text', True),
        "actions": body.get('actions', {}),
        "user_reference": body.get("user_reference", ""),
        "variables_path": body.get('variables_path') or {},
        "names": body.get('names'),
        "suggest": body.get('suggest', False),
        "message_id": str(uuid.uuid1()),
        "reasoning_model": body.get("configuration", {}).get('model') in {'o1-preview', 'o1-mini'},
        "gpt_memory": body.get('gpt_memory'),
        "version_id": body.get('version_id'),
        "gpt_memory_context": body.get('gpt_memory_context'),
        "usage" : {},
        "type" : body.get('configuration',{}).get('type'),
        "apikey_object_id" : body.get('apikey_object_id'),
        "images" : body.get('images'),
        "tool_call_count": body.get('tool_call_count'),
        "tokens" : {},
        "memory" : "",
        "batch" : body.get('batch') or []

    }

def add_default_variables(variables = {}):
    current_time = datetime.now()
    variables['current_time_and_date'] = current_time.strftime("%H:%M:%S") + '_' + current_time.strftime("%Y-%m-%d")
    return variables

def initialize_timer(state: Dict[str, Any]) -> Timer:
    timer_obj = Timer()
    timer_obj.defaultStart(state.get('timer', []))
    return timer_obj

async def load_model_configuration(model, configuration):
    modelname = model.replace("-", "_").replace(".", "_")
    modelfunc = getattr(ModelsConfig, modelname, None)
    if not modelfunc:
        raise ValueError(f"Model {model} not found in ModelsConfig.")
    
    model_obj = modelfunc()
    model_config = model_obj['configuration']
    model_output_config = model_obj['outputConfig']
    
    custom_config = {}
    for key, config in model_config.items():
        if key == 'type':
            continue
        if config["level"] == 2 or key in configuration:
            custom_config[key] = configuration.get(key, config["default"])
    
    return model_obj, custom_config, model_output_config

async def handle_fine_tune_model(parsed_data, custom_config):
    if parsed_data['configuration']['type'] == 'chat' and parsed_data['fine_tune_model'] and \
       parsed_data['model'] in {'gpt-4o-mini-2024-07-18', 'gpt-4o-2024-08-06', 'gpt-4-0613'}:
        custom_config['model'] = parsed_data['fine_tune_model']

async def handle_pre_tools(parsed_data):
    if parsed_data['pre_tools']:
        pre_function_response = await axios_work(
            parsed_data['pre_tools'].get('args', {}),
            parsed_data['pre_tools'].get('name', '')
        )
        if pre_function_response.get('status') == 0:
            parsed_data['variables']['pre_function'] = f"Error while calling prefunction. Error message: {pre_function_response.get('response')}"
        else:
            parsed_data['variables']['pre_function'] = pre_function_response.get('response')

async def manage_threads(parsed_data):
    thread_id = parsed_data['thread_id']
    sub_thread_id = parsed_data['sub_thread_id']
    bridge_id = parsed_data['bridge_id']
    bridge_type = parsed_data['bridgeType']
    org_id = parsed_data['org_id']
    
    if thread_id:
        thread_id = thread_id.strip()
        result = await getThread(thread_id, sub_thread_id, org_id, bridge_id, bridge_type)
        if result["success"]:
            parsed_data['configuration']["conversation"] = result.get("data", [])
    else:
        thread_id = str(uuid.uuid1())
        sub_thread_id = thread_id
        parsed_data['gpt_memory'] = False
        result = {"success": True}
    
    return {
        "thread_id": thread_id,
        "sub_thread_id": sub_thread_id,
        "result": result
    }

async def prepare_prompt(parsed_data, thread_info, model_config, custom_config):
    configuration = parsed_data['configuration']
    variables = parsed_data['variables']
    template = parsed_data['template']
    bridge_type = parsed_data['bridgeType']
    suggest = parsed_data['suggest']
    gpt_memory = parsed_data['gpt_memory']
    memory = None
    
    if configuration['type'] == 'chat':
        id = f"{thread_info['thread_id']}_{parsed_data.get('bridge_id') or parsed_data.get('version_id')}"
        parsed_data['id'] = id
        if gpt_memory:
            response, _ = await fetch("https://flow.sokt.io/func/scriCJLHynCG", "POST", None, None, {"threadID": id})
            if isinstance(response, str):
                memory = response
                parsed_data['memory'] = memory
        configuration['prompt'], missing_vars = Helper.replace_variables_in_prompt(configuration['prompt'], variables)
        
        if template:
            system_prompt = template
            configuration['prompt'], missing_vars = Helper.replace_variables_in_prompt(
                system_prompt, {"system_prompt": configuration['prompt'], **variables}
            )
        
        if bridge_type and model_config.get('response_type') and suggest:
            template_content = (await ConfigurationService.get_template_by_id(Config.CHATBOT_OPTIONS_TEMPLATE_ID)).get('template', '')
            configuration['prompt'], missing_vars = Helper.replace_variables_in_prompt(
                template_content, {"system_prompt": configuration['prompt']}
            )
            custom_config['response_type'] = {"type": "json_object"}
        
        if not parsed_data['is_playground'] and bridge_type is None and model_config.get('response_type'):
            res = parsed_data['body'].get('response_type') or parsed_data['body'].get('configuration',{}).get('response_type',{"type": 'json_object'})
            match res:
                case "default":
                    custom_config['response_type'] = {"type": 'json_object'}
                case "text":
                    custom_config['response_type'] = {"type": 'text'}
                case _:
                    custom_config['response_type'] = res
        
        return memory, missing_vars
    
    return memory, []

async def configure_custom_settings(model_configuration, custom_config, service):
    return await model_config_change(model_configuration, custom_config, service)

def build_service_params(parsed_data, custom_config, model_output_config, thread_info, timer, memory):
    token_calculator = {}
    if not parsed_data['is_playground']:
        token_calculator = TokenCalculator(parsed_data['service'], model_output_config)
    
    return {
        "customConfig": custom_config,
        "configuration": parsed_data['configuration'],
        "apikey": parsed_data['apikey'],
        "variables": parsed_data['variables'],
        "user": parsed_data['user'],
        "tools": parsed_data['tools'],
        "org_id": parsed_data['org_id'],
        "bridge_id": parsed_data['bridge_id'],
        "bridge": parsed_data['bridge'],
        "thread_id": thread_info['thread_id'],
        "sub_thread_id": thread_info['sub_thread_id'],
        "model": parsed_data['model'],
        "service": parsed_data['service'],
        "modelOutputConfig": model_output_config,
        "playground": parsed_data['is_playground'],
        "template": parsed_data['template'],
        "response_format": parsed_data['response_format'],
        "execution_time_logs": {},
        "timer": timer,
        "variables_path": parsed_data['variables_path'],
        "message_id": parsed_data['message_id'],
        "bridgeType": parsed_data['bridgeType'],
        "names": parsed_data['names'],
        "reasoning_model": parsed_data['reasoning_model'],
        "memory": memory,
        "type": parsed_data['configuration'].get('type'),
        "token_calculator": token_calculator,
        "apikey_object_id" : parsed_data['apikey_object_id'],
        "images" : parsed_data['images'],
        "tool_call_count": parsed_data['tool_call_count']
    }

async def process_background_tasks(parsed_data, result):
    tasks = [
            sendResponse(parsed_data['response_format'], result["modelResponse"], success=True, variables=parsed_data.get('variables',{})),
            metrics_service.create([parsed_data['usage']], result["historyParams"], parsed_data['version_id']),
            validateResponse(final_response=result['modelResponse'], configration=parsed_data['configuration'], bridgeId=parsed_data['bridge_id'], message_id=parsed_data['message_id'], org_id=parsed_data['org_id'])
        ]
    if parsed_data['gpt_memory'] and parsed_data['configuration']['type'] == 'chat':
            tasks.append(handle_gpt_memory(parsed_data['id'], parsed_data['user'], result['modelResponse'], parsed_data['memory'], parsed_data['gpt_memory_context']))
    await asyncio.gather(*tasks, return_exceptions=True)

def build_service_params_for_batch(parsed_data, custom_config, model_output_config):
    token_calculator = {}
    if not parsed_data['is_playground']:
        token_calculator = TokenCalculator(parsed_data['service'], model_output_config)
    
    return {
        "customConfig": custom_config,
        "configuration": parsed_data['configuration'],
        "apikey": parsed_data['apikey'],
        "variables": parsed_data['variables'],
        "user": parsed_data['user'],
        "tools": parsed_data['tools'],
        "org_id": parsed_data['org_id'],
        "bridge_id": parsed_data['bridge_id'],
        "bridge": parsed_data['bridge'],
        "model": parsed_data['model'],
        "service": parsed_data['service'],
        "modelOutputConfig": model_output_config,
        "playground": parsed_data['is_playground'],
        "template": parsed_data['template'],
        "response_format": parsed_data['response_format'],
        "execution_time_logs": {},
        "variables_path": parsed_data['variables_path'],
        "message_id": parsed_data['message_id'],
        "bridgeType": parsed_data['bridgeType'],
        "names": parsed_data['names'],
        "reasoning_model": parsed_data['reasoning_model'],
        "type": parsed_data['configuration'].get('type'),
        "token_calculator": token_calculator,
        "apikey_object_id" : parsed_data['apikey_object_id'],
        "batch" : parsed_data['batch']
    }