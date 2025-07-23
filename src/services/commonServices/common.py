from fastapi import FastAPI
from fastapi.responses import JSONResponse
import traceback
from ...db_services import metrics_service as metrics_service
import pydash as _
from ..utils.helper import Helper
from .baseService.utils import sendResponse
from ..utils.ai_middleware_format import Response_formatter
from ..utils.send_error_webhook import send_error_to_webhook
from src.handler.executionHandler import handle_exceptions
from models.mongo_connection import db
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
    create_history_params
)
from src.services.utils.rich_text_support import process_chatbot_response
app = FastAPI()
from src.services.utils.helper import Helper
from src.services.commonServices.testcases import run_testcases as run_bridge_testcases
from globals import *

configurationModel = db["configurations"]

@app.post("/chat/{bridge_id}")
@handle_exceptions
async def chat(request_body): 
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)

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
        raise ValueError(error)
    

async def embedding(request_body):
    result = {}
    try:
        body = request_body.get('body')
        configuration = body.get('configuration')
        text = body.get('text')
        model = configuration.get('model')
        service = body.get('service')
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
            "apikey" : body.get('apikey')
        }

        class_obj = await Helper.embedding_service_handler(params, service)
        result = await class_obj.execute_embedding()

        if not result["success"]:
            raise ValueError(result)
        
        result['modelResponse'] = await Response_formatter(response = result["response"], service = service, type =configuration.get('type'))

        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})
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
                result['response']['data']['message_id'] = parsed_data['message_id']
            await sendResponse(parsed_data['response_format'], result["response"], success=True, variables=parsed_data.get('variables',{}))
            # Update usage metrics for successful API calls
            update_usage_metrics(parsed_data, params, latency, result=result, success=True)
            await process_background_tasks(parsed_data, result, params, None)
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
        raise ValueError(error)
