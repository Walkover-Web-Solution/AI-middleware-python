from openai import AsyncOpenAI
import traceback
import copy
from ..api_executor import execute_api_call
from ..baseService.utils import send_message
# from src.services.utils.unified_token_validator import validate_openai_token_limit
from globals import *


def remove_duplicate_ids_from_input(configuration):
    """
    Remove duplicate items with same IDs from the input array to prevent OpenAI API errors
    """
    config_copy = copy.deepcopy(configuration)
    
    if 'input' not in config_copy:
        return config_copy
    
    input_array = config_copy['input']
    seen_ids = set()
    
    # Filter out duplicate items instead of creating new IDs
    filtered_input = []
    
    for item in input_array:
        if isinstance(item, dict) and 'id' in item:
            original_id = item['id']
            # If ID is duplicate, skip this item (remove it)
            if original_id in seen_ids:
                logger.info(f"Removing duplicate item with ID: {original_id}")
                continue  # Skip this duplicate item
            else:
                seen_ids.add(original_id)
                filtered_input.append(item)
        else:
            # Items without ID are always included
            filtered_input.append(item)
    
    # Update the configuration with filtered input
    config_copy['input'] = filtered_input
    
    return config_copy


async def openai_test_model(configuration, api_key):
    openAI = AsyncOpenAI(api_key=api_key)
    try:
        chat_completion = await openAI.chat.completions.create(**configuration)
        return {'success': True, 'response': chat_completion.to_dict()}
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'status_code': getattr(error, 'status_code', None)
        }


async def stream_openai_response(client, configuration, response_format, execution_time_logs, service, count):
    """
    Stream OpenAI response. If tool call is detected, return full response without streaming.
    If no tool call, stream text deltas via RTLayer.
    """
    config = copy.deepcopy(configuration)
    config['stream'] = True
    
    # Track if we have a tool call
    has_tool_call = False
    
    # Collect all events to build final response
    collected_events = []
    final_response = None
    
    # Track streamed text for building response
    streamed_text = ""
    current_item_id = None
    
    try:
        stream = await client.responses.create(**config)
        
        async for event in stream:
            event_dict = event.to_dict() if hasattr(event, 'to_dict') else event
            event_type = event_dict.get('type', '')
            collected_events.append(event_dict)
            
            # Check for tool call (function_call)
            if event_type == 'response.output_item.added':
                item = event_dict.get('item', {})
                if item.get('type') == 'function_call':
                    has_tool_call = True
                    logger.info("Tool call detected, switching to non-streaming mode")
            
            # Handle text delta streaming (only if no tool call)
            if event_type == 'response.output_text.delta' and not has_tool_call:
                delta = event_dict.get('delta', '')
                streamed_text += delta
                current_item_id = event_dict.get('item_id')
                
                # Stream the delta to RTLayer
                if response_format and response_format.get('type') == 'RTLayer':
                    stream_data = {
                        'type': 'delta',
                        'delta': delta,
                        'item_id': current_item_id,
                        'content_index': event_dict.get('content_index', 0),
                        'output_index': event_dict.get('output_index', 0)
                    }
                    await send_message(cred=response_format['cred'], data={'streaming': True, 'chunk': stream_data, 'success': True})
            
            # Capture the final response
            if event_type == 'response.completed':
                final_response = event_dict.get('response', {})
                
                # Send stream end signal with the complete response
                if not has_tool_call and response_format and response_format.get('type') == 'RTLayer':
                    # First send streaming done signal
                    await send_message(cred=response_format['cred'], data={'streaming': True, 'done': True, 'success': True})
        
        if final_response:
            return {
                'success': True,
                'response': final_response
            }
        else:
            # Build response from collected events if response.completed wasn't received
            return {
                'success': False,
                'error': 'Stream completed without final response',
                'status_code': None
            }
            
    except Exception as error:
        error_str = str(error)
        traceback.print_exc()
        
        # Send error to RTLayer if streaming was active
        if response_format and response_format.get('type') == 'RTLayer':
            await send_message(cred=response_format['cred'], data={'streaming': True, 'error': error_str, 'success': False})
        
        return {
            'success': False,
            'error': error_str,
            'status_code': getattr(error, 'status_code', None)
        }


async def openai_response_model(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name="", org_name="", service="", count=0, token_calculator=None, response_format=None, stream=False):
    try:
        client = AsyncOpenAI(api_key=apiKey)
        
        # Determine if streaming should be enabled
        # Stream only if: stream=True AND response_format is RTLayer
        should_stream = (
            stream and
            response_format and 
            response_format.get('type') == 'RTLayer'
        )
        
        if should_stream:
            # Use streaming mode
            timer.start()
            
            async def streaming_api_call_with_retry(config, max_retries=2):
                current_config = copy.deepcopy(config)
                
                for attempt in range(max_retries + 1):
                    try:
                        result = await stream_openai_response(
                            client, 
                            current_config, 
                            response_format, 
                            execution_time_logs, 
                            service, 
                            count
                        )
                        return result
                    except Exception as error:
                        error_str = str(error)
                        
                        # Check if it's a duplicate item error
                        if "Duplicate item found with id" in error_str and attempt < max_retries:
                            logger.warning(f"Duplicate ID error detected on attempt {attempt + 1}: {error_str}")
                            logger.info("Attempting to fix duplicate IDs and retry...")
                            
                            current_config = remove_duplicate_ids_from_input(current_config)
                            
                            execution_time_logs.append({
                                "step": f"{service} Retry attempt {attempt + 1} - Fixed duplicate IDs", 
                                "time_taken": 0
                            })
                            continue
                        else:
                            traceback.print_exc()
                            return {
                                'success': False,
                                'error': error_str,
                                'status_code': getattr(error, 'status_code', None)
                            }
                
                return {
                    'success': False,
                    'error': 'Max retries exceeded',
                    'status_code': None
                }
            
            result = await streaming_api_call_with_retry(configuration)
            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            
            if result['success']:
                from ..api_executor import check_space_issue
                result['response'] = await check_space_issue(result['response'], service)
                token_calculator.calculate_usage(result['response'])
            
            return result
        else:
            # Use non-streaming mode (original behavior)
            
            # Define the API call function with retry mechanism for duplicate ID errors
            async def api_call_with_retry(config, max_retries=2):
                current_config = copy.deepcopy(config)
                
                for attempt in range(max_retries + 1):
                    try:
                        responses = await client.responses.create(**current_config)
                        return {'success': True, 'response': responses.to_dict()}
                    except Exception as error:
                        error_str = str(error)
                        
                        # Check if it's a duplicate item error
                        if "Duplicate item found with id" in error_str and attempt < max_retries:
                            logger.warning(f"Duplicate ID error detected on attempt {attempt + 1}: {error_str}")
                            logger.info("Attempting to fix duplicate IDs and retry...")
                            
                            # Remove duplicate IDs and regenerate unique ones
                            current_config = remove_duplicate_ids_from_input(current_config)
                            
                            # Log the retry attempt
                            execution_time_logs.append({
                                "step": f"{service} Retry attempt {attempt + 1} - Fixed duplicate IDs", 
                                "time_taken": 0
                            })
                            
                            continue  # Retry with fixed configuration
                        else:
                            # For non-duplicate errors or max retries reached, return the error
                            traceback.print_exc()
                            return {
                                'success': False,
                                'error': error_str,
                                'status_code': getattr(error, 'status_code', None)
                            }
                
                # This should never be reached, but just in case
                return {
                    'success': False,
                    'error': 'Max retries exceeded',
                    'status_code': None
                }

            # Define the API call function for execute_api_call
            async def api_call(config):
                return await api_call_with_retry(config)

            # Execute API call with monitoring
            return await execute_api_call(
                configuration=configuration,
                api_call=api_call,
                execution_time_logs=execution_time_logs,
                timer=timer,
                bridge_id=bridge_id,
                message_id=message_id,
                org_id=org_id,
                alert_on_retry=True,
                name=name,
                org_name=org_name,
                service=service,
                count=count,
                token_calculator=token_calculator
            )

    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }


async def openai_completion(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name="", org_name="", service="", count=0, token_calculator=None, response_format=None, stream=False):
    try:
        openAI = AsyncOpenAI(api_key=apiKey)

        # Define the API call function
        async def api_call(config):
            try:
                chat_completion = await openAI.chat.completions.create(**config)
                return {'success': True, 'response': chat_completion.to_dict()}
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'status_code', None)
                }

        # Execute API call with monitoring
        return await execute_api_call(
            configuration=configuration,
            api_call=api_call,
            execution_time_logs=execution_time_logs,
            timer=timer,
            bridge_id=bridge_id,
            message_id=message_id,
            org_id=org_id,
            alert_on_retry=True,
            name=name,
            org_name=org_name,
            service=service,
            count=count,
            token_calculator=token_calculator
        )

    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }