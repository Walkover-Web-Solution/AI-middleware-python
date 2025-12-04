from openai import AsyncOpenAI
import traceback
import copy
from ..api_executor import execute_api_call
from ..baseService.utils import send_message
from globals import *


async def stream_ai_ml_response(client, configuration, response_format, execution_time_logs, service, count):
    """
    Stream AI/ML response. If tool call is detected, return full response without streaming.
    If no tool call, stream text deltas via RTLayer.
    """
    config = copy.deepcopy(configuration)
    config['stream'] = True
    
    # Track if we have a tool call
    has_tool_call = False
    
    # Build accumulated response
    accumulated_response = {
        'id': '',
        'object': 'chat.completion',
        'created': 0,
        'model': config.get('model', ''),
        'choices': [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': '',
                'tool_calls': None
            },
            'finish_reason': None
        }],
        'usage': None
    }
    
    streamed_content = ""
    tool_calls_data = []
    
    try:
        stream = await client.chat.completions.create(**config)
        
        async for chunk in stream:
            chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
            
            # Update response metadata
            if chunk_dict.get('id'):
                accumulated_response['id'] = chunk_dict['id']
            if chunk_dict.get('created'):
                accumulated_response['created'] = chunk_dict['created']
            if chunk_dict.get('model'):
                accumulated_response['model'] = chunk_dict['model']
            
            choices = chunk_dict.get('choices', [])
            if choices:
                choice = choices[0]
                delta = choice.get('delta', {})
                
                # Check for tool calls
                if delta.get('tool_calls'):
                    has_tool_call = True
                    for tool_call in delta['tool_calls']:
                        index = tool_call.get('index', 0)
                        # Extend tool_calls_data if needed
                        while len(tool_calls_data) <= index:
                            tool_calls_data.append({
                                'id': '',
                                'type': 'function',
                                'function': {'name': '', 'arguments': ''}
                            })
                        # Accumulate tool call data
                        if tool_call.get('id'):
                            tool_calls_data[index]['id'] = tool_call['id']
                        if tool_call.get('function', {}).get('name'):
                            tool_calls_data[index]['function']['name'] = tool_call['function']['name']
                        if tool_call.get('function', {}).get('arguments'):
                            tool_calls_data[index]['function']['arguments'] += tool_call['function']['arguments']
                
                # Handle content delta (only stream if no tool call)
                content_delta = delta.get('content', '')
                if content_delta and not has_tool_call:
                    streamed_content += content_delta
                    
                    # Stream the delta to RTLayer
                    if response_format and response_format.get('type') == 'RTLayer':
                        stream_data = {
                            'type': 'delta',
                            'delta': content_delta
                        }
                        await send_message(cred=response_format['cred'], data={'streaming': True, 'chunk': stream_data, 'success': True})
                elif content_delta:
                    streamed_content += content_delta
                
                # Check finish reason
                if choice.get('finish_reason'):
                    accumulated_response['choices'][0]['finish_reason'] = choice['finish_reason']
            
            # Capture usage if present
            if chunk_dict.get('usage'):
                accumulated_response['usage'] = chunk_dict['usage']
        
        # Build final response
        accumulated_response['choices'][0]['message']['content'] = streamed_content
        if tool_calls_data:
            accumulated_response['choices'][0]['message']['tool_calls'] = tool_calls_data
        
        # Send stream end signal
        if not has_tool_call and response_format and response_format.get('type') == 'RTLayer':
            await send_message(cred=response_format['cred'], data={'streaming': True, 'done': True, 'success': True})
        
        return {
            'success': True,
            'response': accumulated_response
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


async def yield_ai_ml_response(client, configuration, service, count, execution_time_logs, timer, token_calculator):
    """
    Yield AI/ML response chunks for API streaming.
    Accumulates full response for usage calculation and logging.
    """
    config = copy.deepcopy(configuration)
    config['stream'] = True
    
    # Build accumulated response structure
    accumulated_response = {
        'id': '',
        'object': 'chat.completion',
        'created': 0,
        'model': config.get('model', ''),
        'choices': [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': '',
                'tool_calls': None
            },
            'finish_reason': None
        }],
        'usage': None
    }
    
    streamed_content = ""
    tool_calls_data = []
    has_tool_call = False
    
    try:
        stream = await client.chat.completions.create(**config)
        
        async for chunk in stream:
            chunk_dict = chunk.to_dict() if hasattr(chunk, 'to_dict') else chunk
            
            # Update response metadata
            if chunk_dict.get('id'):
                accumulated_response['id'] = chunk_dict['id']
            if chunk_dict.get('created'):
                accumulated_response['created'] = chunk_dict['created']
            if chunk_dict.get('model'):
                accumulated_response['model'] = chunk_dict['model']
            
            choices = chunk_dict.get('choices', [])
            if choices:
                choice = choices[0]
                delta = choice.get('delta', {})
                
                # Check for tool calls
                if delta.get('tool_calls'):
                    has_tool_call = True
                    for tool_call in delta['tool_calls']:
                        index = tool_call.get('index', 0)
                        while len(tool_calls_data) <= index:
                            tool_calls_data.append({
                                'id': '',
                                'type': 'function',
                                'function': {'name': '', 'arguments': ''}
                            })
                        if tool_call.get('id'):
                            tool_calls_data[index]['id'] = tool_call['id']
                        if tool_call.get('function', {}).get('name'):
                            tool_calls_data[index]['function']['name'] = tool_call['function']['name']
                        if tool_call.get('function', {}).get('arguments'):
                            tool_calls_data[index]['function']['arguments'] += tool_call['function']['arguments']

                # Handle content delta
                content_delta = delta.get('content', '')
                if content_delta:
                    streamed_content += content_delta
                
                # Check finish reason
                if choice.get('finish_reason'):
                    accumulated_response['choices'][0]['finish_reason'] = choice['finish_reason']
            
            # Capture usage if present
            if chunk_dict.get('usage'):
                accumulated_response['usage'] = chunk_dict['usage']
            
            # Yield the chunk to the client
            yield chunk_dict

        # Finalize accumulated response
        accumulated_response['choices'][0]['message']['content'] = streamed_content
        if tool_calls_data:
            accumulated_response['choices'][0]['message']['tool_calls'] = tool_calls_data
            
        # Post-processing (logging, usage calculation)
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        
        # We can't easily do check_space_issue here for the stream itself, 
        # but we can run it on the final accumulated response if needed for side effects or logging?
        # Typically check_space_issue modifies the response. Since we already streamed, we can't modify what was sent.
        # But we can still calculate usage.
        
        if token_calculator:
            token_calculator.calculate_usage(accumulated_response)
            
        # Yield final response for internal use (wrapper should filter this out)
        yield {'_internal_final_response': accumulated_response}

    except Exception as error:
        error_str = str(error)
        traceback.print_exc()
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        # Yield error structure if possible, or just raise
        # If we raise, the caller (FastAPI/framework) handles it.
        raise error


async def ai_ml_model_run(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name="", org_name="", service="", count=0, token_calculator=None, response_format=None, stream=False):
    try:
        openAI = AsyncOpenAI(api_key=apiKey, base_url='https://api.ai.ml/openai')
        
        # Determine streaming mode
        is_rtlayer_stream = stream and response_format and response_format.get('type') == 'RTLayer'
        is_api_stream = stream and not is_rtlayer_stream
        
        if is_rtlayer_stream:
            # Use RTLayer streaming
            timer.start()
            
            result = await stream_ai_ml_response(
                openAI,
                configuration,
                response_format,
                execution_time_logs,
                service,
                count
            )
            
            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            
            if result['success']:
                from ..api_executor import check_space_issue
                result['response'] = await check_space_issue(result['response'], service)
                token_calculator.calculate_usage(result['response'])
            
            return result
            
        elif is_api_stream:
            # Use API streaming (yield chunks)
            timer.start()
            return yield_ai_ml_response(
                openAI,
                configuration,
                service,
                count,
                execution_time_logs,
                timer,
                token_calculator
            )
            
        else:
            # Use non-streaming mode (original behavior)

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