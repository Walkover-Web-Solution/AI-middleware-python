import json
import uuid
import traceback
from typing import Any, Dict
from fastapi.responses import JSONResponse
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
from src.services.cache_service import make_json_serializable, find_in_cache
from src.configs.model_configuration import model_config_document
from globals import *
from src.services.utils.send_error_webhook import send_error_to_webhook
from src.services.commonServices.queueService.queueLogService import sub_queue_obj
from src.services.commonServices.baseService.utils import make_request_data_and_publish_sub_queue
from src.db_services.metrics_service import create
from src.controllers.conversationController import save_sub_thread_id_and_name
from src.services.utils.ai_middleware_format import send_alert
from src.services.cache_service import find_in_cache, store_in_cache, client, REDIS_PREFIX
from ..commonServices.baseService.utils import sendResponse
from src.services.utils.rich_text_support import process_chatbot_response
from src.db_services.orchestrator_history_service import OrchestratorHistoryService, orchestrator_collector

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
        "org_id": state.get('profile', {}).get('org', {}).get('id', '') or body.get('org_id'),
        "user": body.get("user"),
        "tools": body.get("configuration", {}).get('tools'),
        "service": body.get("service"),
        "variables": body.get("variables") or {},
        "bridgeType": body.get('chatbot'),
        "template": body.get('template'),
        "response_format": body.get("configuration", {}).get("response_format"),
        "response_type": body.get("configuration", {}).get("response_type"),
        "model": body.get("configuration", {}).get('model'),
        "is_playground": state.get('is_playground') or body.get('is_playground') or False,
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
        "fall_back" : body.get('fall_back') or {},
        "guardrails" : body.get('bridges', {}).get('guardrails') or {},
        "testcase_data" : body.get('testcase_data') or {},
        "file_data" : body.get('video_data') or {},
        "youtube_url" : body.get('youtube_url') or None
    }



def add_default_template(prompt):
    prompt += ' \n if you need current time in any case (otherwise ignore) - {{current_time_date_and_current_identifier}}'
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
        if "level" in config and (config["level"] == 0 or config["level"] == 1 or config["level"] == 2) or key in configuration:
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
        
        # Check Redis cache first for conversations
        version_id = parsed_data.get('version_id', '')
        redis_key = f"conversation_{version_id}_{thread_id}_{sub_thread_id}"
        cached_conversations = await find_in_cache(redis_key)
        
        if cached_conversations:
            # Use cached conversations from Redis
            parsed_data['configuration']["conversation"] = json.loads(cached_conversations)
            result = json.loads(cached_conversations)
            logger.info(f"Retrieved conversations from Redis cache: {redis_key}")
        else:
            # Fallback to database if not in cache
            result = await try_catch(getThread, thread_id, sub_thread_id, org_id, bridge_id, bridge_type)
            if result:
                parsed_data['configuration']["conversation"] = result or []
    else:
        thread_id = str(uuid.uuid1())
        sub_thread_id = thread_id
        parsed_data['gpt_memory'] = False
        result = []
    
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

def build_service_params(parsed_data, custom_config, model_output_config, thread_info=None, timer=None, memory=None, send_error_to_webhook=None):
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
        "thread_id": thread_info['thread_id'] if thread_info else parsed_data['thread_id'],
        "sub_thread_id": thread_info['sub_thread_id'] if thread_info else parsed_data['sub_thread_id'],
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
        "files" : parsed_data['files'],
        "file_data" : parsed_data['file_data'],
        "youtube_url" : parsed_data['youtube_url']

    }

async def process_background_tasks(parsed_data, result, params, thread_info):
    asyncio.create_task(create([parsed_data['usage']], result["historyParams"], parsed_data['version_id'], thread_info))
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
            # Handle if variables_state is None
            if variables_state is None:
                return missing_vars
            
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
        case 'openai':
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
    # Safely get overall time without overriding original errors
    over_all_time = 0.00
    try:
        if hasattr(timer, "start_times") and timer.start_times:
            over_all_time = timer.stop("Api total time")
    except Exception:
        # Silently fail to avoid overriding original error
        pass
    
    return {
        "over_all_time": over_all_time,
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
        "expectedCost": parsed_data['tokens'].get('total_cost', 0),
        "variables": parsed_data.get('variables') or {},
        "outputTokens": result.get('response', {}).get('usage', {}).get('output_tokens', 0) or 0 if result else 0,
        "inputTokens": result.get('response', {}).get('usage', {}).get('input_tokens', 0) or 0 if result else 0,
        "total_tokens": result.get('response', {}).get('usage', {}).get('total_tokens', 0) or 0 if result else 0
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


def add_child_agents_as_tools(agent_config, orchestrator_data):
    """
    Add child agents as tools to the agent configuration
    
    Args:
        agent_config: Current agent configuration
        orchestrator_data: Full orchestrator data with agents info
    
    Returns:
        Updated agent configuration with child agent tools
    """
    agent_info = agent_config.get('agent_info', {})
    child_agents = agent_info.get('childAgents', [])
    
    if not child_agents:
        return agent_config
    
    # Initialize tools if not present
    if 'tools' not in agent_config['configuration']:
        agent_config['configuration']['tools'] = []
    
    # Add each child agent as a tool
    for child_agent_id in child_agents:
        child_info = orchestrator_data.get('agents', {}).get(child_agent_id, {})
        if child_info:
            name = f"call_{child_info.get('name', 'agent').replace(' ', '_').lower()}"
            description = f"{child_info.get('description', 'Connected agent')})"
            
            tool = {
                "type": "function",
                "name": name,
                "description": description,
                "properties": {
                    "user_query": {
                        "description": "The query to send to the child agent",
                        "type": "string",
                        "enum": [],
                        "required_params": [],
                        "parameter": {}
                    },
                    "action_type": {
                        "description": "transfer: directly return child agent response, conversation: get child response and continue processing",
                        "type": "string",
                        "enum": ["transfer", "conversation"],
                        "required_params": [],
                        "parameter": {}
                    }
                },
                "required": ["user_query", "action_type"]
            }
            
            agent_config['configuration']['tools'].append(tool)
            
            # Add to tool mapping
            if 'tool_id_and_name_mapping' not in agent_config:
                agent_config['tool_id_and_name_mapping'] = {}
            
            agent_config['tool_id_and_name_mapping'][name] = {
                "type": "AGENT",
                "agent_id": child_agent_id
            }
    
    return agent_config

def update_orchestration_prompt(agent_config):
    """
    Update agent prompt to include orchestration instructions
    
    Args:
        agent_config: Agent configuration to update
    
    Returns:
        Updated agent configuration with orchestration prompt
    """
    original_prompt = agent_config['configuration'].get('prompt', '')
    
    orchestration_instructions = """

You are an orchestrator agent with access to child agents through function calls. You have two interaction modes:

1. **TRANSFER**: Use when you want to directly transfer the user's query to a child agent and return their response immediately.
2. **CONVERSATION**: Use when you want to get information from a child agent and then provide your own response based on that information.

When calling child agents:
- Use "transfer" action_type to directly return the child agent's response
- Use "conversation" action_type to get child agent's response and continue processing

If you don't need any child agents, respond directly to the user's query.
"""
    
    agent_config['configuration']['prompt'] = original_prompt + orchestration_instructions
    return agent_config

async def orchestrator_agent_chat(agent_config, body=None, user=None):
    """
    Process individual agent configuration with same flow as chat function
    
    Args:
        agent_config: Agent configuration from orchestrator data
        request_body_data: Original request body data for context
    
    Returns:
        Chat response for the agent
    """
    result = {}
    class_obj = {}
    orchestrator_data = body.get('orchestrator_data')
    try:
        # Add child agents as tools if orchestrator_data is provided
        if orchestrator_data:
            agent_config = add_child_agents_as_tools(agent_config, orchestrator_data)
            agent_config = update_orchestration_prompt(agent_config)
        
        # Add user query to variables if provided
        if user:
            if 'variables' not in agent_config:
                agent_config['variables'] = {}
            agent_config['variables']['user_query'] = user
        
        # Initialize orchestrator data collection session
        thread_id = body.get('thread_id')
        org_id = body.get('org_id')
        # Pick orchestrator_id with proper fallbacks
        orchestrator_id =  body.get('orchestrator_id')
        
        # Use thread_id as primary session key, fallback to a global session key
        session_key = thread_id if thread_id else f"global_orchestrator_{org_id}"
        if session_key and org_id:
            if not orchestrator_collector.get_session_data(session_key):
                orchestrator_collector.initialize_session(session_key, org_id, orchestrator_id)
    
        request_data = {
            "body": {
                "configuration": agent_config.get("configuration", {}),
                "model": agent_config.get("configuration", {}).get("model"),
                "service": agent_config.get("service"),
                "apikey": agent_config.get("apikey"),
                "bridge_id": agent_config.get("bridge_id"),
                "version_id": agent_config.get("version_id"),
                "org_id": body.get("org_id"),
                "pre_tools": agent_config.get("pre_tools"),
                "org_name" : agent_config.get("org_name"),
                "name" : agent_config.get("name"),
                "variables": agent_config.get("variables", {}),
                "variables_path": agent_config.get("variables_path", {}),
                "rag_data": agent_config.get("rag_data", []),
                "actions": agent_config.get("actions", []),
                "files": [],
                "message": user,
                "thread_id": body.get('thread_id'),
                "sub_thread_id": body.get('sub_thread_id') or body.get('thread_id'),
                "message_id": f"orchestrator_{agent_config.get('bridge_id', 'unknown')}",
                "user": user,
                "tool_id_and_name_mapping": agent_config.get('tool_id_and_name_mapping', {}),
                "apikey_object_id": agent_config.get("apikey_object_id"),
                "gpt_memory": agent_config.get("gpt_memory"),
                "gpt_memory_context": agent_config.get("gpt_memory_context"),
                "tool_call_count": agent_config.get("tool_call_count"),
                "RTLayer": agent_config.get("RTLayer"),
                "user_reference": agent_config.get("user_reference"),

            },
            "state": {
                "profile": {
                    "org": {
                        "id": body.get("org_id", "")
                    }
                },
                "timer":body.get('state', {}).get("timer", []),
                "isPlayground": False
            },
            "path_params": {}
        }
        
        # Step 1: Parse and validate request body (directly pass the data)
        parsed_data = parse_request_body(request_data)

        parsed_data['configuration']['prompt'] = add_default_template(parsed_data.get('configuration', {}).get('prompt', ''))
        parsed_data['variables'] = add_user_in_varaibles(parsed_data['variables'], parsed_data['user'])
        
        # Step 2: Initialize Timer
        timer = initialize_timer(parsed_data['state'])
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration'], parsed_data['service'],
        )
        
        # Step 4: Handle Fine Tune Model
        await handle_fine_tune_model(parsed_data, custom_config)

        # Step 5: Handle Pre-Tools Execution
        await handle_pre_tools(parsed_data)

        # Step 6: Manage Threads
        thread_info = await manage_threads(parsed_data)
        
        # Add Files from cache if Present
        if len(parsed_data['files']) == 0:
            parsed_data['files'] = await add_files_to_parse_data(parsed_data['thread_id'], parsed_data['sub_thread_id'], parsed_data['bridge_id'])

        # Step 7: Prepare Prompt, Variables and Memory
        memory, missing_vars = await prepare_prompt(parsed_data, thread_info, model_config, custom_config)
        
        missing_vars = filter_missing_vars(missing_vars, parsed_data['variables_state'])

        # Handle missing variables
        if missing_vars:
            send_error(parsed_data['bridge_id'], parsed_data['org_id'], missing_vars, error_type='Variable')
        
        # Step 8: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        
        # Step 9: Execute Service Handler
        params = build_service_params(
            parsed_data, custom_config, model_output_config, thread_info, timer, memory, send_error_to_webhook
        )
        
        # Step 10: json_schema service conversion
        if 'response_type' in custom_config and custom_config['response_type'].get('type') == 'json_schema':
            custom_config['response_type'] = restructure_json_schema(custom_config['response_type'], parsed_data['service'])
        
        class_obj = await Helper.create_service_handler(params, parsed_data['service'])
        result = await class_obj.execute()
            
        if not result["success"]:
            raise ValueError(result)
        
        if result['modelResponse'].get('firstAttemptError'):
            send_error(parsed_data['bridge_id'], parsed_data['org_id'], result['modelResponse']['firstAttemptError'], error_type='retry_mechanism')
        
        if parsed_data['configuration']['type'] == 'chat':
            if parsed_data['is_rich_text'] and parsed_data['bridgeType'] and parsed_data['reasoning_model'] == False:
                try:
                    await process_chatbot_response(result, params, parsed_data, model_output_config, timer, params['execution_time_logs'])
                except Exception as e:
                    raise RuntimeError(f"error in chatbot : {e}")
                    
        parsed_data['alert_flag'] = result['modelResponse'].get('alert_flag', False)    
        if not parsed_data['is_playground']:
            result['response']['usage'] = params['token_calculator'].get_total_usage()
            
        if parsed_data.get('type') != 'image':
            parsed_data['tokens'] = Helper.calculate_usage(parsed_data['model'],result["response"],parsed_data['service'])
            
        # Create latency object using utility function
        latency = create_latency_object(timer, params)
        
        if not parsed_data['is_playground']:
            if result.get('response') and result['response'].get('data'):
                result['response']['data']['message_id'] = parsed_data['message_id']
            await sendResponse(parsed_data['response_format'], result["response"], success=True, variables=parsed_data.get('variables',{}))
            # Update usage metrics for successful API calls
            update_usage_metrics(parsed_data, params, latency, result=result, success=True)
            await process_background_tasks(parsed_data, result, params, thread_info)
        

        # Collect orchestrator data before processing result
        bridge_id = agent_config.get('bridge_id')
        if bridge_id and result.get('success'):
            # Extract data from result and parsed_data
            orchestrator_data_to_store = {
                'model_name': parsed_data.get('model'),
                'user': user,
                'response': result.get('response', {}).get('data', {}).get('content', ''),
                'tool_call_data': result.get('response', {}).get('data', {}).get('tool_data', ''),
                'latency': latency if 'latency' in locals() else None,
                'tokens': parsed_data.get('tokens'),
                'error': {'status': False, 'message': None},
                'variables': parsed_data.get('variables', {}),
                'image_urls': parsed_data.get('files', []) if parsed_data.get('files') else [],
                'ai_config': params.get('custom_config', {})
            }
            
            # Add data to collector using consistent session_key
            session_key = thread_id if thread_id else f"global_orchestrator_{org_id}"
            if not orchestrator_collector.get_session_data(session_key):
                # Initialize session if not already done
                orchestrator_collector.initialize_session(session_key, org_id, orchestrator_id)
            orchestrator_collector.add_bridge_data(session_key, bridge_id, orchestrator_data_to_store)
        # Check if there are tool calls that need orchestration
        if result.get('transfer_agent_config'):
            return await handle_orchestration_tool_calls(
                result, agent_config, body, user
            )
        current_agent_id = agent_config.get('bridge_id')
        cache_key = f"orchestrator_{parsed_data['thread_id']}_{parsed_data['sub_thread_id']}"
        await store_in_cache(cache_key, current_agent_id)
        
        # Save orchestrator history to PostgreSQL before returning
        # Only save when this is the final agent call (no transfer_agent_config)
        if bridge_id and result.get('success') and not result.get('transfer_agent_config'):
            session_key = thread_id if thread_id else f"global_orchestrator_{org_id}"
            session_data = orchestrator_collector.get_session_data(session_key)
            if session_data:
                try:
                    await OrchestratorHistoryService.save_orchestrator_history(session_data)
                    # Clear session data after saving
                    orchestrator_collector.clear_session(session_key)
                except Exception as e:
                    logger.error(f"Failed to save orchestrator history: {str(e)}")
        
        return JSONResponse(status_code=200, content={"success": True, "response": result["response"]})
        
    except (Exception, ValueError, BadRequestException) as error:
        if not isinstance(error, BadRequestException):
            logger.error(f'Error in orchestrator_agent_chat: %s, {str(error)}, {traceback.format_exc()}')
        
        # Collect error data for orchestrator history
        if 'bridge_id' in locals() and bridge_id:
            error_data = {
                'model_name': parsed_data.get('model') if 'parsed_data' in locals() else None,
                'user': user,
                'error': {'status': True, 'message': str(error)},
                'variables': parsed_data.get('variables', {}) if 'parsed_data' in locals() else {},
                'latency': latency if 'latency' in locals() else None,
                'tokens': None,
                'tool_call_data': None,
                'image_urls': [],
                'ai_config': params.get('custom_config', {})
            }
            org_id = body.get('org_id') if 'body' in locals() else 'unknown'
            session_key = thread_id if 'thread_id' in locals() and thread_id else f"global_orchestrator_{org_id}"
            if not orchestrator_collector.get_session_data(session_key):
                # Initialize session if not already done
                final_orchestrator_id = bridge_id or 'error_orchestrator'  # Use bridge_id as fallback
                orchestrator_collector.initialize_session(session_key, org_id, final_orchestrator_id)
            orchestrator_collector.add_bridge_data(session_key, bridge_id, error_data)
        
        if not parsed_data['is_playground']:
            # Create latency object and update usage metrics
            latency = create_latency_object(timer, params)
            update_usage_metrics(parsed_data, params, latency, error=error, success=False)
            
            # Create history parameters
            parsed_data['historyParams'] = create_history_params(parsed_data, error, class_obj)
            await sendResponse(parsed_data['response_format'], result.get("modelResponse", str(error)), variables=parsed_data['variables']) if parsed_data['response_format']['type'] != 'default' else None
            # Process background tasks for error handling
            await process_background_tasks_for_error(parsed_data, error)
        
        # Save orchestrator history even in error cases
        if 'bridge_id' in locals() and bridge_id:
            org_id = body.get('org_id') if 'body' in locals() else 'unknown'
            session_key = thread_id if 'thread_id' in locals() and thread_id else f"global_orchestrator_{org_id}"
            session_data = orchestrator_collector.get_session_data(session_key)
            if session_data:
                try:
                    await OrchestratorHistoryService.save_orchestrator_history(session_data)
                    # Clear session data after saving
                    orchestrator_collector.clear_session(session_key)
                except Exception as e:
                    logger.error(f"Failed to save orchestrator history in error case: {str(e)}")
        
        # Add support contact information to error message
        error_message = f"{str(error)}. For more support contact us at support@gtwy.ai"
        print(f"Error in orchestrator_agent_chat: {error_message}")
        raise ValueError(error_message)


async def handle_orchestration_tool_calls(result, current_agent_config, orchestrator_data, user_query):
    """
    Handle tool calls for orchestration (child agent calls) or transfer_agent_config
    
    Args:
        result: Current agent's response with tool calls or transfer_agent_config
        current_agent_config: Current agent configuration
        orchestrator_data: Full orchestrator data
        user_query: Original user query
    
    Returns:
        Final response after orchestration
    """
    # Check if we have transfer_agent_config (new transfer object)
    if result.get('transfer_agent_config'):
        transfer_config = result.get('transfer_agent_config')
        
        # Extract data from transfer_agent_config object
        child_agent_id = transfer_config.get('agent_id')
        action_type = transfer_config.get('action_type', 'transfer')
        child_query = transfer_config.get('user_query', user_query)
        
        print(f"Transfer detected - calling child agent {child_agent_id} with action: {action_type}")
        
        # Get child agent configuration
        child_agent_config = orchestrator_data.get('agent_configurations', {}).get(child_agent_id)
        if not child_agent_config:
            print(f"Child agent configuration not found for {child_agent_id}")
            return result
        
        # Call child agent directly with transfer
        child_response = await orchestrator_agent_chat(
            child_agent_config, orchestrator_data, child_query
        )
        
        # For transfer action, return child agent response immediately
        print(f"Transferring to child agent {child_agent_id}")
        return child_response
    
    # Handle legacy tool_calls format
    tool_calls = result.get('response', {}).get('data', {}).get('tool_calls', [])
    
    for tool_call in tool_calls:
        function_name = tool_call.get('function', {}).get('name', '')
        function_args = json.loads(tool_call.get('function', {}).get('arguments', '{}'))
        
        # Check if this is an agent tool call
        tool_mapping = current_agent_config.get('tool_id_and_name_mapping', {})
        if function_name in tool_mapping and tool_mapping[function_name].get('type') == 'AGENT':
            child_agent_id = tool_mapping[function_name]['agent_id']
            action_type = function_args.get('action_type', 'conversation')
            child_query = function_args.get('user_query', user_query)
            
            print(f"Calling child agent {child_agent_id} with action: {action_type}")
            
            # Get child agent configuration
            child_agent_config = orchestrator_data.get('agent_configurations', {}).get(child_agent_id)
            if not child_agent_config:
                continue
            
            # Call child agent
            child_response = await orchestrator_agent_chat(
                child_agent_config, orchestrator_data, child_query
            )
            
            # Handle response based on action type
            if action_type == 'transfer':
                # Direct transfer - return child agent response immediately
                print(f"Transferring to child agent {child_agent_id}")
                return child_response
            
            elif action_type == 'conversation':
                # Conversation mode - continue with current agent using child response
                print(f"Got response from child agent {child_agent_id}, continuing conversation")
                
                # Extract child response content
                child_content = ""
                if hasattr(child_response, 'body'):
                    child_data = await child_response.body
                    child_json = json.loads(child_data)
                    child_content = child_json.get('response', {}).get('data', {}).get('message', '')
                else:
                    child_content = str(child_response)
                
                # Update current agent's conversation with child response
                conversation_prompt = f"""
Child agent response: {child_content}

Based on the child agent's response above, please provide your final answer to the user's original query: {user_query}
"""
                
                # Create new agent call with child response context
                updated_agent_config = current_agent_config.copy()
                updated_agent_config['configuration']['prompt'] = conversation_prompt
                
                # Remove tools to prevent recursive calls
                if 'tools' in updated_agent_config['configuration']:
                    del updated_agent_config['configuration']['tools']
                
                # Call current agent again with child response context
                final_response = await orchestrator_agent_chat(
                    updated_agent_config, orchestrator_data, user_query
                )
                
                return final_response
    
    # If no agent tool calls found, return original response
    return JSONResponse(status_code=200, content={"success": True, "response": result["response"]})

async def process_background_tasks_for_playground(result, parsed_data):
    from src.controllers.testcase_controller import handle_playground_testcase
    from bson import ObjectId
    
    try:
        testcase_data = parsed_data.get('testcase_data', {})
        
        # If testcase_id exists, update in background and return immediately
        if testcase_data.get('testcase_id'):
            Flag = False
            # Update testcase in background (async task)
            async def update_testcase_background():
                try:
                    await handle_playground_testcase(result, parsed_data, Flag)
                except Exception as e:
                    logger.error(f"Error updating testcase in background: {str(e)}")
            
            asyncio.create_task(update_testcase_background())
        
        else:
            # Generate testcase_id immediately and add to response
            new_testcase_id = str(ObjectId())
            result['response']['testcase_id'] = new_testcase_id
            
            # Add the generated ID to testcase_data for the background task
            parsed_data['testcase_data']['testcase_id'] = new_testcase_id
            
            # Save testcase data in background using the same function
            async def create_testcase_background():
                try:
                    Flag = True
                    await handle_playground_testcase(result, parsed_data, Flag)
                except Exception as e:
                    logger.error(f"Error creating testcase in background: {str(e)}")
            
            asyncio.create_task(create_testcase_background())
                
    except Exception as e:
        logger.error(f"Error processing playground testcase: {str(e)}")
    


