import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import traceback
from ...db_services import metrics_service as metrics_service
import pydash as _
from ..utils.helper import Helper
import asyncio
from .baseService.utils import sendResponse
from ..utils.ai_middleware_format import Response_formatter, send_alert
from ..utils.send_error_webhook import send_error_to_webhook
import json
from src.handler.executionHandler import handle_exceptions
from models.mongo_connection import db
from src.services.utils.common_utils import parse_request_body, initialize_timer, load_model_configuration, handle_pre_tools, handle_fine_tune_model,manage_threads, prepare_prompt, configure_custom_settings, build_service_params, process_background_tasks, add_default_variables, build_service_params_for_batch
from src.services.utils.rich_text_support import process_chatbot_response
app = FastAPI()
from src.services.utils.helper import Helper
configurationModel = db["configurations"]

@app.post("/chat/{bridge_id}")
@handle_exceptions
async def chat(request_body): 
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)
        #  add defualt varaibles in prompt eg : time and date
        parsed_data['variables'] = add_default_variables(parsed_data['variables'])
        # Step 2: Initialize Timer
        timer = initialize_timer(parsed_data['state'])
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration']
        )
        # Step 3: Load Model Configuration
        await handle_fine_tune_model(parsed_data, custom_config)

        # Step 4: Handle Pre-Tools Execution
        await handle_pre_tools(parsed_data)

        # Step 5: Manage Threads
        thread_info = await manage_threads(parsed_data)

        # Step 6: Prepare Prompt, Variables and Memory
        memory, missing_vars = await prepare_prompt(parsed_data, thread_info, model_config, custom_config)
        
        # Handle missing variables
        if missing_vars:
            await send_error_to_webhook(
                parsed_data['bridge_id'], parsed_data['org_id'], missing_vars, error_type='Variable'
            )
        
        # Step 7: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        # Step 8: Execute Service Handler
        params = build_service_params(
            parsed_data, custom_config, model_output_config, thread_info, timer, memory
        )

        class_obj = await Helper.create_service_handler(params, parsed_data['service'])
        result = await class_obj.execute()
            
        if not result["success"]:
            raise ValueError(result)
        
        if parsed_data['configuration']['type'] == 'chat':
            if parsed_data['is_rich_text'] and parsed_data['bridgeType'] and parsed_data['reasoning_model'] == False:
                try:
                    await process_chatbot_response(result, params, parsed_data, model_config, model_output_config)
                except Exception as e:
                    print(f"error in chatbot : {e}")
                    raise RuntimeError(f"error in chatbot : {e}")
            
        if parsed_data['version'] == 2:
            result['modelResponse'] = await Response_formatter(result["modelResponse"], parsed_data['service'], result["historyParams"].get('tools', {}), parsed_data['type'], parsed_data['images'])
            if not parsed_data['is_playground']:
                result['modelResponse']['usage'] = params['token_calculator'].get_total_usage()
            if parsed_data.get('type') != 'image':
                parsed_data['tokens'] = Helper.calculate_usage(parsed_data['model'],result["modelResponse"],parsed_data['service'])
        latency = {
            "over_all_time": timer.stop("Api total time") or "",
            "model_execution_time": sum(params['execution_time_logs'].values()) or "",
            "execution_time_logs": params['execution_time_logs'] or {}
        }
        
        if not parsed_data['is_playground']:
            parsed_data['usage'].update({
                **result.get("usage", {}),
                "service": parsed_data['service'],
                "model": parsed_data['model'],
                "orgId": parsed_data['org_id'],
                "latency": json.dumps(latency),
                "success": True,
                "variables": parsed_data['variables'],
                "prompt": parsed_data['configuration'].get("prompt") or "",
                "apikey_object_id": params['apikey_object_id'],
                "expectedCost" : parsed_data['tokens'].get('expectedCost',0)
            })
            if result.get('modelResponse') and result['modelResponse'].get('data'):
                result['modelResponse']['data']['message_id'] = parsed_data['message_id']
            asyncio.create_task(process_background_tasks(parsed_data, result))
        return JSONResponse(status_code=200, content={"success": True, "response": result["modelResponse"]})
    except Exception as error:
        traceback.print_exc()
        if not parsed_data['is_playground']:
            latency = {
                "over_all_time": timer.stop("Api total time") or "",
                "model_execution_time": sum(params['execution_time_logs'].values()) or "",
                "execution_time_logs": params['execution_time_logs'] or {}
            }
            parsed_data['usage'].update({
                **parsed_data['usage'],
                "service": parsed_data['service'],
                "model": parsed_data['model'],
                "orgId": parsed_data['org_id'],
                "latency": json.dumps(latency),
                "success": False,
                "error": str(error),
                "apikey_object_id": params['apikey_object_id'],
                "expectedCost" : parsed_data['tokens'].get('expectedCost',0),
                "variables" : parsed_data.get('variables') or {}
            })
            # Combine the tasks into a single asyncio.gather call
            tasks = [
                metrics_service.create([parsed_data['usage']], {
                    "thread_id": parsed_data['thread_id'],
                    "sub_thread_id": parsed_data['sub_thread_id'],
                    "user": parsed_data['user'],
                    "message": "",
                    "org_id": parsed_data['org_id'],
                    "bridge_id": parsed_data['bridge_id'],
                    "model": parsed_data['model'] or parsed_data['configuration'].get("model", None),
                    "channel": 'chat',
                    "type": "error",
                    "actor": "user",
                    "message_id": parsed_data['message_id'],
                    "AiConfig": class_obj.aiconfig()
                    }, parsed_data['version_id']),
                # Only send the second response if the type is not 'default'
                sendResponse(parsed_data['response_format'], result.get("modelResponse", str(error)), variables=parsed_data['variables']) if parsed_data['response_format']['type'] != 'default' else None,
                send_alert(data={"configuration": parsed_data['configuration'], "error": str(error), "message_id": parsed_data['message_id'], "bridge_id": parsed_data['bridge_id'], "message": "Exception for the code", "org_id": parsed_data['org_id']}),
            ]
            # Filter out None values
            await asyncio.gather(*[task for task in tasks if task is not None], return_exceptions=True)
            print("chat common error=>", error)
        raise ValueError(error)
    

async def batch(request_body):
    result ={}
    class_obj= {}
    try:
        # Step 1: Parse and validate request body
        parsed_data = parse_request_body(request_body)
        #  add defualt varaibles in prompt eg : time and date
        parsed_data['variables'] = add_default_variables(parsed_data['variables'])
        
        # Step 3: Load Model Configuration
        model_config, custom_config, model_output_config = await load_model_configuration(
            parsed_data['model'], parsed_data['configuration']
        )

        # Step 4: Handle Pre-Tools Execution
        await handle_pre_tools(parsed_data)
        
        # Step 7: Configure Custom Settings
        custom_config = await configure_custom_settings(
            model_config['configuration'], custom_config, parsed_data['service']
        )
        # Step 8: Execute Service Handler
        params = build_service_params_for_batch( parsed_data, custom_config, model_output_config )
        class_obj = await Helper.create_service_handler_for_batch(params, parsed_data['service'])
        result = await class_obj.batch_execute()
            
        if not result["success"]:
            raise ValueError(result)
        
        return JSONResponse(status_code=200, content={"success": True, "response": result["message"]})
    except Exception as error:
        raise ValueError(error)