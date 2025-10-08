from fastapi import FastAPI
from fastapi.responses import JSONResponse
import traceback
from typing import Any, Dict, Optional
from ...db_services import metrics_service as metrics_service
import pydash as _
from ..utils.helper import Helper
from .baseService.utils import sendResponse
from ..utils.ai_middleware_format import Response_formatter
from ..utils.send_error_webhook import send_error_to_webhook
from src.handler.executionHandler import handle_exceptions
from models.mongo_connection import db
import json
from src.services.utils.common_utils import (
    parse_request_body,
    initialize_timer,
    load_model_configuration,
    handle_pre_tools,
    handle_fine_tune_model,
    manage_threads,
    prepare_prompt,
    configure_custom_settings,
    build_service_params,
    build_service_params_for_batch,
    add_default_template,
    filter_missing_vars,
    send_error,
    restructure_json_schema,
    process_background_tasks,
    add_user_in_varaibles,
    process_background_tasks_for_error,
    update_usage_metrics,
    create_latency_object,
    create_history_params,
    add_files_to_parse_data,
    orchestrator_agent_chat,
    process_background_tasks_for_playground,
    compute_embedding_cost
)
from src.services.utils.guardrails_validator import guardrails_check
from src.services.utils.rich_text_support import process_chatbot_response
app = FastAPI()
from src.services.utils.helper import Helper
from src.services.commonServices.testcases import run_testcases as run_bridge_testcases
from globals import *
from src.services.cache_service import find_in_cache
from src.db_services.embed_user_limit_service import (
    get_embed_usage_limits,
    record_embed_usage_cost,
    build_limit_summary,
)

configurationModel = db["configurations"]

@app.post("/chat/{bridge_id}")
@handle_exceptions
async def chat(request_body): 
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)
        if parsed_data.get('guardrails',{}).get('is_enabled', False):
            guardrails_result = await guardrails_check(parsed_data)
            if guardrails_result is not None:
                # Content was blocked by guardrails, return the blocked response
                return JSONResponse(status_code=200, content=guardrails_result)

        parsed_data['configuration']['prompt'] = add_default_template(parsed_data.get('configuration', {}).get('prompt', ''))
        parsed_data['variables'] = add_user_in_varaibles(parsed_data['variables'], parsed_data['user'])
        # Step 2: Initialize Timer
        timer = initialize_timer(parsed_data['state'])
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration'], parsed_data['service'],
        )
        # Step 3: Load Model Configuration
        await handle_fine_tune_model(parsed_data, custom_config)

        # Step 4: Handle Pre-Tools Execution
        await handle_pre_tools(parsed_data)

        # Step 5: Manage Threads
        thread_info = await manage_threads(parsed_data)
        # add Files from cache is Present
        if len(parsed_data['files']) == 0:
            parsed_data['files'] = await add_files_to_parse_data(parsed_data['thread_id'], parsed_data['sub_thread_id'], parsed_data['bridge_id'])

        # Step 6: Prepare Prompt, Variables and Memory
        memory, missing_vars = await prepare_prompt(parsed_data, thread_info, model_config, custom_config)
        

        missing_vars = filter_missing_vars(missing_vars, parsed_data['variables_state'])

        # Handle missing variables
        if missing_vars:
            send_error(parsed_data['bridge_id'], parsed_data['org_id'], missing_vars, error_type='Variable')
        
        # Step 7: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        # Step 8: Execute Service Handler
        params = build_service_params(
            parsed_data, custom_config, model_output_config, thread_info, timer, memory, send_error_to_webhook
        )
        # Step 9 : json_schema service conversion
        if 'response_type' in custom_config and custom_config['response_type'].get('type') == 'json_schema':
            custom_config['response_type'] = restructure_json_schema(custom_config['response_type'], parsed_data['service'])
        
        
        # Execute with retry mechanism
        class_obj = await Helper.create_service_handler(params, parsed_data['service'])
        
        try:
            result = await class_obj.execute()
            result['response']['usage'] = params['token_calculator'].get_total_usage()
            execution_failed = not result["success"]
            original_error = result.get('error', 'Unknown error') if execution_failed else None
        except Exception as execution_exception:
            # Handle exceptions during execution
            execution_failed = True
            original_error = str(execution_exception)
            result = {
                "success": False,
                "error": original_error,
                "response": {"usage": {}},
                "modelResponse": {}
            }
        
        # Retry mechanism with fallback configuration
        if execution_failed and parsed_data.get('fall_back'):
            try:
                # Store original configuration
                fallback_config = parsed_data['fall_back']
                original_model = parsed_data['model']
                original_service = parsed_data['service']
                
                # Update parsed_data with fallback configuration
                parsed_data['model'] = fallback_config.get('model', parsed_data['model'])
                parsed_data['service'] = fallback_config.get('service', parsed_data['service'])
                parsed_data['configuration']['model'] = fallback_config.get('model')
                # Check if service has changed - if so, create new service handler
                if parsed_data['service'] != original_service:
                    parsed_data['apikey'] = fallback_config.get('apikey')
                    
                    # Load fresh model configuration for the fallback service and model
                    fallback_model_config, fallback_custom_config, fallback_model_output_config = await load_model_configuration(
                        parsed_data['model'], parsed_data['configuration'], parsed_data['service']
                    )
            
                    # Configure custom settings specifically for the fallback service
                    fallback_custom_config = await configure_custom_settings(
                        fallback_model_config['configuration'], fallback_custom_config, parsed_data['service']
                    )
                    params = build_service_params(
                        parsed_data, fallback_custom_config, fallback_model_output_config, thread_info, timer, memory, send_error_to_webhook
                    )
                    # Step 9 : json_schema service conversion
                    if 'response_type' in fallback_custom_config and fallback_custom_config['response_type'].get('type') == 'json_schema':
                        fallback_custom_config['response_type'] = restructure_json_schema(fallback_custom_config['response_type'], parsed_data['service'])
                    
                    # Create new service handler for the fallback service
                    class_obj = await Helper.create_service_handler(params, parsed_data['service'])
                else:
                    # Same service, just update existing class_obj
                    class_obj.model = parsed_data['model']
                    if fallback_config.get('apikey'):
                        class_obj.apikey = fallback_config['apikey']
                    
                    # Reconfigure custom_config for fallback service
                    class_obj.customConfig = await configure_custom_settings(
                        model_config['configuration'], custom_config, parsed_data['service']
                    )
                
                # Execute with updated configuration
                result = await class_obj.execute()
                result['response']['usage'] = params['token_calculator'].get_total_usage()
                
                # Mark that this was a retry attempt and store original error
                if result["success"]:
                    result['modelResponse']['firstAttemptError'] = f"Original attempt failed with {original_service}/{original_model}: {original_error}. Retried with {parsed_data['service']}/{parsed_data['model']}"
                
            except Exception as retry_error:
                # If retry also fails, restore original configuration and continue with original error
                parsed_data['model'] = original_model
                parsed_data['service'] = original_service
                # Note: We don't need to restore class_obj properties since we may have created a new object
                logger.error(f"Retry mechanism failed: {str(retry_error)}")
        
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
        if parsed_data.get('type') != 'image':
            parsed_data['tokens'] = params['token_calculator'].calculate_total_cost(parsed_data['model'], parsed_data['service'])
            result['response']['usage']['cost'] = parsed_data['tokens'].get('total_cost') or 0
            result['response']['data']['message_id'] = parsed_data['message_id']
        # Create latency object using utility function
        latency = create_latency_object(timer, params)
        if not parsed_data['is_playground']:
            if result.get('response') and result['response'].get('data'):
                result['response']['data']['message_id'] = parsed_data['message_id']
            await sendResponse(parsed_data['response_format'], result["response"], success=True, variables=parsed_data.get('variables',{}))
            # Update usage metrics for successful API calls
            update_usage_metrics(parsed_data, params, latency, result=result, success=True)
            result['response']['usage']['cost'] = parsed_data['usage'].get('expectedCost', 0)
            await process_background_tasks(parsed_data, result, params, thread_info)
        else:
            if parsed_data.get('testcase_data',{}).get('run_testcase', False):
                from src.services.commonServices.testcases import process_single_testcase_result
                # Process testcase result and add score to response
                testcase_result = await process_single_testcase_result(
                    parsed_data.get('testcase_data', {}), 
                    result, 
                    parsed_data
                )
                result['response']['testcase_result'] = testcase_result
            else:
                await process_background_tasks_for_playground(result, parsed_data)
        return JSONResponse(status_code=200, content={"success": True, "response": result["response"]})
    
    except (Exception, ValueError, BadRequestException) as error:
        if not isinstance(error, BadRequestException):
            logger.error(f'Error in chat service: %s, {str(error)}, {traceback.format_exc()}')
        if not parsed_data['is_playground']:
            # Create latency object and update usage metrics
            latency = create_latency_object(timer, params)
            update_usage_metrics(parsed_data, params, latency, error=error, success=False)
            
            # Create history parameters
            parsed_data['historyParams'] = create_history_params(parsed_data, error, class_obj)
            await sendResponse(parsed_data['response_format'], result.get("modelResponse", str(error)), variables=parsed_data['variables']) if parsed_data['response_format']['type'] != 'default' else None
            # Process background tasks for error handling
            await process_background_tasks_for_error(parsed_data, error)
        # Add support contact information to error message
        error_message = f"{str(error)}. For more support contact us at support@gtwy.ai"
        raise ValueError(error_message)



@handle_exceptions
async def orchestrator_chat(request_body): 
    try:
        body = request_body.get('body',{})
        # Extract user query from the request
        user = body.get('user')
        thread_id = body.get('thread_id')
        sub_thread_id = body.get('sub_thread_id', thread_id)
        body['state'] = request_body.get('state', {})

        master_agent_id = None
        master_agent_config = None
        
        # First try to find in Redis cache
        if thread_id and sub_thread_id:
            cached_agent = await find_in_cache(f"orchestrator_{thread_id}_{sub_thread_id}")
            if cached_agent:
                master_agent_id = json.loads(cached_agent)
                master_agent_config = body.get('agent_configurations', {}).get(master_agent_id)
        
        # If not found in cache, get from request body
        if not master_agent_id or not master_agent_config:
            master_agent_id = body.get('master_agent_id')
            master_agent_config = body.get('master_agent_config')
        
        if not master_agent_id or not master_agent_config:
            raise ValueError("Master agent configuration not found")
        
        # Call master agent with orchestration capabilities directly
        response = await orchestrator_agent_chat(master_agent_config, body, user)
        return response
        
    except (Exception, ValueError, BadRequestException) as error:
        print(f"Error in orchestrator_chat: {str(error)}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(error)})

async def embedding(request_body):
    result = {}
    limit_context = {"user": None, "org": None}
    try:
        body = request_body.get('body') or {}
        state = request_body.get('state') or {}
        profile = state.get('profile') or {}
        user_info = profile.get('user') or {}
        org_info = profile.get('org') or {}

        configuration = body.get('configuration', {})
        text = body.get('text')
        model = configuration.get('model')
        service = body.get('service')

        # Determine embed user context
        is_embed_user = state.get('embed')
        if is_embed_user is None:
            meta = user_info.get('meta')
            if isinstance(meta, dict):
                is_embed_user = meta.get('type') == 'embed'
            else:
                is_embed_user = user_info.get('is_embedUser')

        org_id = state.get('org_id') or org_info.get('id') or body.get('org_id')
        user_id = state.get('user_id') or user_info.get('id')
        folder_id = state.get('folder_id')
        if not folder_id:
            meta = user_info.get('meta')
            if isinstance(meta, dict):
                folder_id = meta.get('folder_id')

        # Pre-fetch usage records (user + org scopes) to enforce limits
        if is_embed_user and org_id:
            limit_context = await get_embed_usage_limits(org_id, user_id, folder_id)

            user_record = limit_context.get("user")
            org_record = limit_context.get("org")

            async def limit_summary(record: Dict[str, Any]) -> Dict[str, Any]:
                summary = await build_limit_summary(record)
                summary["limit_reached"] = True
                return summary

            def is_limit_exhausted(record: Optional[Dict[str, Any]]) -> bool:
                if not record or not record.get('is_active', True):
                    return False
                limit_value = record.get('limit')
                if limit_value is None:
                    return False
                consumed_value = float(record.get('consumed', 0.0) or 0.0)
                try:
                    limit_float = float(limit_value)
                except (TypeError, ValueError):
                    return False
                return consumed_value >= limit_float

            exhausted_user = user_record if is_limit_exhausted(user_record) else None
            exhausted_org = org_record if is_limit_exhausted(org_record) else None

            if exhausted_user or exhausted_org:
                usage_details: Dict[str, Any] = {"limit_reached": True}
                if exhausted_user:
                    usage_details["user_limit"] = await limit_summary(exhausted_user)
                if exhausted_org:
                    usage_details["org_limit"] = await limit_summary(exhausted_org)

                return JSONResponse(
                    status_code=402,
                    content={
                        "success": False,
                        "error": "Embed cost limit exceeded",
                        "usage": usage_details,
                    },
                )

        model_config, custom_config, model_output_config = await load_model_configuration(model, configuration, service)
        chatbot = body.get('chatbot')
        if chatbot:
            raise ValueError("Error: Embedding not supported for chatbot")
        params = {
            "model": model,
            "configuration": configuration,
            "model_config": model_config,
            "customConfig": custom_config,
            "model_output_config": model_output_config,
            "text": text,
            "response_format": configuration.get("response_format") or {},
            "service": service,
            "version_id": body.get('version_id'),
            "bridge_id": body.get('bridge_id'),
            "org_id": body.get('org_id'),
            "apikey": body.get('apikey')
        }

        class_obj = await Helper.embedding_service_handler(params, service)
        result = await class_obj.execute_embedding()

        if not result["success"]:
            raise ValueError(result)

        usage_data = (result.get("response") or {}).get("usage")
        cost = compute_embedding_cost(model_output_config, usage_data)

        user_record = limit_context.get("user")
        org_record = limit_context.get("org")

        updated_user_record = None
        updated_org_record = None

        if user_record and user_record.get('is_active', True):
            updated_user_record = await record_embed_usage_cost(org_id, user_id, folder_id, cost)
        if org_record and org_record.get('is_active', True):
            updated_org_record = await record_embed_usage_cost(org_id, None, folder_id, cost)

        async def summarize(record: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
            if not record:
                return None
            summary = await build_limit_summary(record)
            if summary.get("limit") is not None:
                summary["limit_reached"] = summary.get("remaining") == 0.0
            return summary

        user_summary = await summarize(updated_user_record or user_record)
        org_summary = await summarize(updated_org_record or org_record)

        usage_response: Dict[str, Any] = {}
        if usage_data:
            usage_response["prompt_tokens"] = usage_data.get("prompt_tokens")
            usage_response["total_tokens"] = usage_data.get("total_tokens")
        usage_response["cost"] = cost

        primary_summary = user_summary or org_summary
        if primary_summary:
            usage_response.update(
                {
                    "limit": primary_summary.get("limit"),
                    "consumed": primary_summary.get("consumed"),
                    "remaining": primary_summary.get("remaining"),
                    "reset_frequency": primary_summary.get("reset_frequency"),
                    "period_start": primary_summary.get("period_start"),
                    "period_end": primary_summary.get("period_end"),
                    "limit_reached": primary_summary.get("limit_reached", False),
                }
            )

        if user_summary:
            usage_response["user_limit"] = user_summary
        if org_summary:
            usage_response["org_limit"] = org_summary

        result['modelResponse'] = await Response_formatter(
            response=result["response"], service=service, type=configuration.get('type')
        )

        response_payload = {"success": True, "response": result["modelResponse"]}
        if usage_response:
            response_payload["usage"] = usage_response

        return JSONResponse(status_code=200, content=response_payload)
    except Exception as error:
        raise ValueError(error)

async def batch(request_body):
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)
        if parsed_data['batch_webhook'] is None:
            raise ValueError("webhook is required")
        #  add defualt varaibles in prompt eg : time and date
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration'], parsed_data['service'],
        )

        # Step 4: Handle Pre-Tools Execution
        await handle_pre_tools(parsed_data)
        
        # Step 7: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        if 'tools' in custom_config:
            del custom_config['tools']
        # Step 8: Execute Service Handler
        params = build_service_params_for_batch( parsed_data, custom_config, model_output_config )
        class_obj = await Helper.create_service_handler_for_batch(params, parsed_data['service'])
        result = await class_obj.batch_execute()
            
        if not result["success"]:
            raise ValueError(result)
        
        return JSONResponse(status_code=200, content={"success": True, "response": result["message"]})
    except Exception as error:
        traceback.print_exc()
        raise ValueError(error)
    
    
async def run_testcases(request_body):
    try:
        parsed_data = parse_request_body(request_body)
        org_id = request_body['state']['profile']['org']['id']
        result = await run_bridge_testcases(parsed_data, org_id, parsed_data['body']['bridge_id'], chat)
        return JSONResponse(content={'success': True, 'response': {'testcases_result': dict(result)}})
    except Exception as error:
        logger.error(f'Error in running testcases, {str(error)}, {traceback.format_exc()}')
        return JSONResponse(status_code=400, content={'success': False, 'error': str(error)})
    

async def image(request_body):
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)

        # Step 2: Initialize Timer
        timer = initialize_timer(parsed_data['state'])
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration'], parsed_data['service'],
        )
        
        # Step 4: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        # Step 5: Manage Threads
        thread_info = await manage_threads(parsed_data)

        # Step 5: Execute Service Handler
        params = build_service_params(
            parsed_data, custom_config, model_output_config, thread_info, timer, None, send_error_to_webhook
        )
        
        
        class_obj = await Helper.create_service_handler(params, parsed_data['service'])
        result = await class_obj.execute()
            
        if not result["success"]:
            raise ValueError(result)

        # Create latency object using utility function
        latency = create_latency_object(timer, params)
        if not parsed_data['is_playground']:
            if result.get('response') and result['response'].get('data'):
                result['response']['data']['id'] = parsed_data['message_id']
            await sendResponse(parsed_data['response_format'], result["response"], success=True, variables=parsed_data.get('variables',{}))
            # Update usage metrics for successful API calls
            update_usage_metrics(parsed_data, params, latency, result=result, success=True)
            await process_background_tasks(parsed_data, result, params, None)
        return JSONResponse(status_code=200, content={"success": True, "response": result["response"]})
    
    except (Exception, ValueError, BadRequestException) as error:
        if not isinstance(error, BadRequestException):
            logger.error(f'Error in image service: {str(error)}, {traceback.format_exc()}')
        if not parsed_data['is_playground']:
            # Create latency object and update usage metrics
            latency = create_latency_object(timer, params)
            update_usage_metrics(parsed_data, params, latency, error=error, success=False)
            
            # Create history parameters
            parsed_data['historyParams'] = create_history_params(parsed_data, error, class_obj)
            await sendResponse(parsed_data['response_format'], result.get("modelResponse", str(error)), variables=parsed_data['variables']) if parsed_data['response_format']['type'] != 'default' else None
            # Process background tasks for error handling
            await process_background_tasks_for_error(parsed_data, error)
        raise ValueError(error)
