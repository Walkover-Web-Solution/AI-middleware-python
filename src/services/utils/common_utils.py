import json
import uuid
from typing import Any, Dict
from src.services.utils.time import Timer
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
from datetime import datetime, timedelta, timezone
from src.services.cache_service import make_json_serializable
from src.configs.model_configuration import model_config_document
from globals import *
from src.services.utils.send_error_webhook import send_error_to_webhook
from src.services.commonServices.queueService.queueLogService import sub_queue_obj
from src.services.commonServices.baseService.utils import make_request_data_and_publish_sub_queue
from src.db_services.metrics_service import create
from src.controllers.conversationController import save_sub_thread_id_and_name
from src.services.utils.ai_middleware_format import send_alert
from src.services.cache_service import find_in_cache, store_in_cache, client, REDIS_PREFIX

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
        "tool_id_and_name_mapping": body.get("tool_id_and_name_mapping"),
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
        "bridge_summary" : body.get('bridge_summary'),
        "batch" : body.get('batch') or [],
        "batch_webhook" : body.get('webhook'),
        "doc_ids":body.get('ddc_ids'),
        "rag_data": body.get('rag_data'),
        "name" : body.get('name'),
        "org_name" : body.get('org_name'),
        "variables_state" : body.get('variables_state'),
        "built_in_tools" : body.get('built_in_tools') or [],
        "thread_flag" : body.get('thread_flag') or False,
        "files" : body.get('files') or [],
    }



def add_default_template(prompt):
    prompt += ' \n Additional Information if requied : For current date and time always refer: {{current_time_date_and_current_identifier}}'
    return prompt

def add_user_in_varaibles(variables, user):
    variables['_user_message'] = user
    return variables

def initialize_timer(state: Dict[str, Any]) -> Timer:
    timer_obj = Timer()
    timer_obj.defaultStart(state.get('timer', []))
    return timer_obj

async def load_model_configuration(model, configuration, service):
    model_obj = model_config_document[service][model]
    if not model_obj:
        raise BadRequestException(f"Model {model} not found in ModelsConfig.")
    
    # model_obj = modelfunc()
    model_config = model_obj['configuration']
    model_output_config = model_obj['outputConfig']
    
    custom_config = {}
    for key, config in model_config.items():
        if key == 'type' or key == 'specification':
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
        parsed_data['pre_tools']['args']['user'] = parsed_data['user']
        pre_function_response = await axios_work(
            parsed_data['pre_tools'].get('args', {}),
            {
                "url":f"https://flow.sokt.io/func/{parsed_data['pre_tools'].get('name')}"
            }
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
        result = await try_catch(getThread, thread_id, sub_thread_id, org_id, bridge_id, bridge_type)
        if result:
            parsed_data['configuration']["conversation"] = result or []
    else:
        thread_id = str(uuid.uuid1())
        sub_thread_id = thread_id
        parsed_data['gpt_memory'] = False
        result = {"success": True}
    
    # cache_key = f"{bridge_id}_{thread_id}_{sub_thread_id}"
    # if len(parsed_data['files']) == 0:
    #     cached_files = await find_in_cache(cache_key)
    #     if cached_files:
    #         parsed_data['files'] = json.loads(cached_files)
    
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
    
    if configuration['type'] == 'chat' or configuration['type'] == 'reasoning':
        id = f"{thread_info['thread_id']}_{thread_info['sub_thread_id']}_{parsed_data.get('version_id') or parsed_data.get('bridge_id')}"
        parsed_data['id'] = id
        if gpt_memory:
            memory = await find_in_cache(id)
            if memory:
                # Convert bytes to string if needed
                if isinstance(memory, bytes):
                    memory = memory.decode('utf-8')
                parsed_data['memory'] = memory
            else:
                response, _ = await fetch("https://flow.sokt.io/func/scriCJLHynCG", "POST", None, None, {"threadID": id})
                parsed_data['memory'] = response
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
        if parsed_data['bridge_summary']is not None:
            parsed_data['bridge_summary'], missing_vars = Helper.replace_variables_in_prompt(parsed_data['bridge_summary'], variables)
        
        return memory, missing_vars
    
    return memory, []

async def configure_custom_settings(model_configuration, custom_config, service):
    return await model_config_change(model_configuration, custom_config, service)

def build_service_params(parsed_data, custom_config, model_output_config, thread_info, timer, memory, send_error_to_webhook):
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
        "execution_time_logs": [],
        "function_time_logs": [],
        "timer": timer,
        "variables_path": parsed_data['variables_path'],
        "message_id": parsed_data['message_id'],
        "bridgeType": parsed_data['bridgeType'],
        "tool_id_and_name_mapping": parsed_data["tool_id_and_name_mapping"],
        "reasoning_model": parsed_data['reasoning_model'],
        "memory": memory,
        "type": parsed_data['configuration'].get('type'),
        "token_calculator": token_calculator,
        "apikey_object_id" : parsed_data['apikey_object_id'],
        "images" : parsed_data['images'],
        "tool_call_count": parsed_data['tool_call_count'],
        "rag_data": parsed_data['rag_data'],
        "name" : parsed_data['name'],
        "org_name" : parsed_data['org_name'],
        "send_error_to_webhook": send_error_to_webhook,
        "built_in_tools" : parsed_data['built_in_tools'],
        "files" : parsed_data['files']

    }

async def process_background_tasks(parsed_data, result, params, thread_info):
    asyncio.create_task(create([parsed_data['usage']], result["historyParams"], parsed_data['version_id']))
    data = await make_request_data_and_publish_sub_queue(parsed_data, result, params, thread_info)
    data = make_json_serializable(data)
    await sub_queue_obj.publish_message(data)


async def process_background_tasks_for_error(parsed_data, error):
    # Combine the tasks into a single asyncio.gather call
    tasks = [
        send_alert(data={"org_name" : parsed_data['org_name'], "bridge_name" : parsed_data['name'], "configuration": parsed_data['configuration'], "error": str(error), "message_id": parsed_data['message_id'], "bridge_id": parsed_data['bridge_id'], "message": "Exception for the code", "org_id": parsed_data['org_id']}),
        create([parsed_data['usage']],parsed_data['historyParams'] , parsed_data['version_id']),
        save_sub_thread_id_and_name(parsed_data['thread_id'], parsed_data['sub_thread_id'], parsed_data['org_id'], parsed_data['thread_flag'], parsed_data['response_format'], parsed_data['bridge_id'], parsed_data['user'])
    ]
    # Filter out None values
    await asyncio.gather(*[task for task in tasks if task is not None], return_exceptions=True)

def build_service_params_for_batch(parsed_data, custom_config, model_output_config):
    
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
        "execution_time_logs": [],
        "variables_path": parsed_data['variables_path'],
        "message_id": parsed_data['message_id'],
        "bridgeType": parsed_data['bridgeType'],
        "reasoning_model": parsed_data['reasoning_model'],
        "type": parsed_data['configuration'].get('type'),
        "apikey_object_id" : parsed_data['apikey_object_id'],
        "batch" : parsed_data['batch'],
        "webhook" : parsed_data['batch_webhook']
    }


async def updateVariablesWithTimeZone(variables, org_id):
    org_name = ''
    async def getTimezoneOfOrg():
        data = await Helper.get_timezone_and_org_name(org_id)
        timezone = data.get('timezone') or "+5:30"
        hour, minutes = timezone.split(':')
        return int(hour), int(minutes), data.get('name') or "", (data.get('meta') or {}).get('identifier', '')
    hour, minutes, org_name, identifier = await getTimezoneOfOrg()
    if 'timezone' in variables:
        hour, minutes = Helper.get_current_time_with_timezone(variables['timezone'])
        identifier = variables['timezone']
    current_time = datetime.now(timezone.utc)
    current_time = current_time + timedelta(hours=hour, minutes=minutes)
    if identifier == '' and 'timezone' not in variables:
        identifier = 'Asia/Calcutta'
    variables['current_time_date_and_current_identifier'] = current_time.strftime("%Y-%m-%d") + ' ' + current_time.strftime("%H:%M:%S") + ' ' + current_time.strftime("%A") + ' (' + identifier + ')'
    return variables, org_name


def filter_missing_vars(missing_vars, variables_state):
            # Iterate through keys in missing_vars
            keys_to_remove = [key for key, value in variables_state.items() if value != 'required']
            
            # Remove the keys from missing_vars that are in the keys_to_remove list
            for key in keys_to_remove:
                if key in missing_vars:
                    del missing_vars[key]
            
            return missing_vars

def get_service_by_model(model): 
    return next((s for s in model_config_document if model in model_config_document[s]), None)

def send_error(bridge_id, org_id, error_message, error_type):
    asyncio.create_task(send_error_to_webhook(
        bridge_id, org_id, error_message, error_type=error_type
    ))

def restructure_json_schema(response_type, service):
    match service:
        case 'openai_response':
            schema = response_type.get('json_schema', {})
            del response_type['json_schema']
            for key, value in schema.items():
                response_type[key] = value
            return response_type
        case _:
            return response_type


def create_latency_object(timer, params):
    """
    Create a latency metrics object for API usage tracking.
    
    Args:
        timer: Timer object for tracking execution time
        params: Parameters dictionary containing execution logs
        
    Returns:
        Dictionary containing latency metrics
    """
    return {
        "over_all_time": timer.stop("Api total time") if hasattr(timer, "start_times") else "",
        "model_execution_time": sum([log.get("time_taken", 0) for log in params['execution_time_logs']]) or "",
        "execution_time_logs": params['execution_time_logs'] or {},
        "function_time_logs": params['function_time_logs'] or {}
    }


def update_usage_metrics(parsed_data, params, latency, result=None, error=None, success=False):
    """
      be metrics with latency and other information.
    Handles both success and error cases with a unified interface.
    
    Args:
        parsed_data: Dictionary containing parsed request data
        params: Parameters dictionary containing execution logs
        latency: Latency metrics object
        result: Optional result dictionary from the API call (for success case)
        error: Optional error object or string (for error case)
        success: Boolean indicating if the operation was successful
        
    Returns:
        Updated usage dictionary
    """
    # Base fields common to both success and error cases
    update_data = {
        "service": parsed_data['service'],
        "model": parsed_data['model'],
        "orgId": parsed_data['org_id'],
        "latency": json.dumps(latency),
        "success": success,
        "apikey_object_id": params.get('apikey_object_id'),
        "expectedCost": parsed_data['tokens'].get('expectedCost', 0),
        "variables": parsed_data.get('variables') or {}
    }
    
    # Add success-specific fields
    if success and result:
        update_data.update({
            **(result.get("usage", {}) or {}),
            "prompt": parsed_data['configuration'].get("prompt") or ""
        })
    
    # Add error-specific fields
    elif error and not success:
        update_data["error"] = str(error)
    
    # Update the usage dictionary
    parsed_data['usage'].update({
        **parsed_data['usage'],
        **update_data
    })
    
    return parsed_data['usage']


def create_history_params(parsed_data, error=None, class_obj=None):
    """
    Create history parameters for error tracking and logging.
    
    Args:
        parsed_data: Dictionary containing parsed request data
        error: Optional error object
        class_obj: Optional class object with aiconfig method
        
    Returns:
        Dictionary containing history parameters
    """
    return {
        "thread_id": parsed_data['thread_id'],
        "sub_thread_id": parsed_data['sub_thread_id'],
        "user": parsed_data['user'],
        "message": None,
        "org_id": parsed_data['org_id'],
        "bridge_id": parsed_data['bridge_id'],
        "model": parsed_data['model'] or parsed_data['configuration'].get("model", None),
        "channel": 'chat',
        "type": "error",
        "actor": "user",
        'tools_call_data': error.args[1] if error and len(error.args) > 1 else None,
        "message_id": parsed_data['message_id'],
        "AiConfig": class_obj.aiconfig() if class_obj else None
    }


async def add_files_to_parse_data(thread_id, sub_thread_id, bridge_id):
    cache_key = f"{bridge_id}_{thread_id}_{sub_thread_id}"
    files = await find_in_cache(cache_key)
    if files:
        return json.loads(files)
    return []
    
    
        
