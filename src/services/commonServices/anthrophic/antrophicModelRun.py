from anthropic import AsyncAnthropic
import traceback
import json
from ..api_executor import execute_api_call
from ..baseService.utils import send_message
# from src.services.utils.unified_token_validator import validate_anthropic_token_limit
from globals import *


async def yield_anthropic_response(client, configuration, service, count, execution_time_logs, timer, token_calculator):
    """
    Yield Anthropic response chunks for API streaming.
    Accumulates full response for usage calculation and logging.
    """
    config = copy.deepcopy(configuration)
    # Anthropic stream method doesn't use 'stream' param in config, it's a separate method
    if 'stream' in config:
        del config['stream']
        
    # Initialize response structure to accumulate streaming data
    accumulated_response = {
        'id': '',
        'type': 'message',
        'role': 'assistant',
        'content': [],
        'model': config.get('model', ''),
        'stop_reason': None,
        'stop_sequence': None,
        'usage': {'input_tokens': 0, 'output_tokens': 0}
    }
    
    # Track content blocks
    content_blocks = {}
    
    try:
        async with client.messages.stream(**config) as stream_response:
            async for event in stream_response:
                # Yield the raw event if needed, or construct a standardized chunk
                # For now, let's yield a standardized chunk format similar to OpenAI if possible, 
                # or just yield the Anthropic event dict. 
                # To be consistent with other services which yield what the client returns (usually dicts),
                # we'll yield the event as a dict.
                # Anthropic events are objects, need to convert to dict if possible or yield as is.
                # The 'event' object from `messages.stream` might be a wrapper.
                # Let's check the event type.
                
                # Note: `stream_response` yields `MessageStreamEvent` objects.
                # We'll construct a dict representation for the client.
                
                event_type = event.type
                event_dict = {
                    'type': event_type
                }
                
                if event_type == 'message_start':
                    message_data = event.message
                    accumulated_response['id'] = message_data.id
                    accumulated_response['model'] = message_data.model
                    accumulated_response['usage']['input_tokens'] = message_data.usage.input_tokens
                    
                    event_dict['message'] = {
                        'id': message_data.id,
                        'model': message_data.model,
                        'usage': {'input_tokens': message_data.usage.input_tokens}
                    }
                    
                elif event_type == 'content_block_start':
                    index = event.index
                    content_block = event.content_block
                    event_dict['index'] = index
                    event_dict['content_block'] = {'type': content_block.type}
                    
                    if content_block.type == 'text':
                        content_blocks[index] = {'type': 'text', 'text': ''}
                        event_dict['content_block']['text'] = content_block.text
                    elif content_block.type == 'tool_use':
                        initial_input = getattr(content_block, 'input', {}) or {}
                        content_blocks[index] = {
                            'type': 'tool_use',
                            'id': content_block.id,
                            'name': content_block.name,
                            'input': initial_input
                        }
                        event_dict['content_block'].update({
                            'id': content_block.id,
                            'name': content_block.name,
                            'input': initial_input
                        })
                    elif content_block.type == 'thinking':
                        content_blocks[index] = {'type': 'thinking', 'thinking': ''}
                        event_dict['content_block']['thinking'] = content_block.thinking
                        
                elif event_type == 'content_block_delta':
                    index = event.index
                    delta = event.delta
                    event_dict['index'] = index
                    event_dict['delta'] = {'type': delta.type}
                    
                    block = content_blocks.get(index)
                    if block:
                        if delta.type == 'text_delta':
                            block.setdefault('text', '')
                            block['text'] += delta.text
                            event_dict['delta']['text'] = delta.text
                        elif delta.type == 'input_json_delta':
                            block.setdefault('partial_json', '')
                            block['partial_json'] += delta.partial_json
                            event_dict['delta']['partial_json'] = delta.partial_json
                        elif delta.type == 'input_text_delta':
                            block.setdefault('partial_text', '')
                            block['partial_text'] += delta.partial_text
                            event_dict['delta']['partial_text'] = delta.partial_text
                        elif delta.type == 'thinking_delta':
                            block.setdefault('thinking', '')
                            block['thinking'] += delta.thinking
                            event_dict['delta']['thinking'] = delta.thinking
                            
                elif event_type == 'content_block_stop':
                    index = event.index
                    event_dict['index'] = index
                    if index in content_blocks:
                        block = content_blocks[index]
                        if block['type'] == 'tool_use':
                            if 'partial_json' in block:
                                try:
                                    block['input'] = json.loads(block['partial_json']) if block['partial_json'] else {}
                                except json.JSONDecodeError:
                                    block['input'] = block.get('partial_json', {})
                                finally:
                                    del block['partial_json']
                            if 'partial_text' in block:
                                partial_text = block.pop('partial_text')
                                block['input'] = partial_text # Simplified logic
                                
                elif event_type == 'message_delta':
                    delta = event.delta
                    event_dict['delta'] = {}
                    if hasattr(delta, 'stop_reason') and delta.stop_reason:
                        accumulated_response['stop_reason'] = delta.stop_reason
                        event_dict['delta']['stop_reason'] = delta.stop_reason
                    if hasattr(delta, 'stop_sequence') and delta.stop_sequence:
                        accumulated_response['stop_sequence'] = delta.stop_sequence
                        event_dict['delta']['stop_sequence'] = delta.stop_sequence
                    if hasattr(event, 'usage') and event.usage:
                        accumulated_response['usage']['output_tokens'] = event.usage.output_tokens
                        event_dict['usage'] = {'output_tokens': event.usage.output_tokens}
                        
                elif event_type == 'message_stop':
                    pass
                
                # Yield the constructed dict
                yield event_dict

        # Finalize accumulated response
        ordered_content = [content_blocks[i] for i in sorted(content_blocks.keys())]
        merged_content = []
        current_text_block = None

        for block in ordered_content:
            if block.get('type') == 'text':
                if current_text_block is None:
                    current_text_block = {'type': 'text', 'text': block.get('text', '')}
                else:
                    current_text_block['text'] += block.get('text', '')
            else:
                if current_text_block is not None:
                    merged_content.append(current_text_block)
                    current_text_block = None
                merged_content.append(block)

        if current_text_block is not None:
            merged_content.append(current_text_block)

        accumulated_response['content'] = merged_content
        
        # Post-processing
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        
        if token_calculator:
            token_calculator.calculate_usage(accumulated_response)
            
        # Yield final response for internal use
        yield {'_internal_final_response': accumulated_response}

    except Exception as error:
        error_str = str(error)
        traceback.print_exc()
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        raise error


async def anthropic_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer, name="", org_name="", service="", count=0, token_calculator=None, response_format=None, stream=False):
    try:
        # Initialize async client
        anthropic_client = AsyncAnthropic(api_key=apikey)
        
        # Determine streaming mode
        is_rtlayer_stream = stream and response_format and response_format.get('type') == 'RTLayer'
        is_api_stream = stream and not is_rtlayer_stream
        
        if is_api_stream:
            # Use API streaming (yield chunks)
            timer.start()
            return yield_anthropic_response(
                anthropic_client,
                configuration,
                service,
                count,
                execution_time_logs,
                timer,
                token_calculator
            )

        # Determine if streaming to RTLayer should be enabled
        should_stream_to_rtlayer = is_rtlayer_stream

        # Define the API call function with streaming
        async def api_call(config):
            try:
                # Track if we have a tool call
                has_tool_call = False
                
                # Initialize response structure to accumulate streaming data
                accumulated_response = {
                    'id': '',
                    'type': 'message',
                    'role': 'assistant',
                    'content': [],
                    'model': config.get('model', ''),
                    'stop_reason': None,
                    'stop_sequence': None,
                    'usage': {'input_tokens': 0, 'output_tokens': 0}
                }
                
                # Track content blocks
                content_blocks = {}
                
                # Create streaming response (stream method doesn't need 'stream' parameter)
                async with anthropic_client.messages.stream(**config) as stream_response:
                    async for event in stream_response:
                        if event.type == 'message_start':
                            # Initialize message with basic info
                            message_data = event.message
                            accumulated_response['id'] = message_data.id
                            accumulated_response['model'] = message_data.model
                            accumulated_response['usage']['input_tokens'] = message_data.usage.input_tokens
                            
                        elif event.type == 'content_block_start':
                            # Initialize content block
                            index = event.index
                            content_block = event.content_block
                            
                            if content_block.type == 'text':
                                content_blocks[index] = {
                                    'type': 'text',
                                    'text': ''
                                }
                            elif content_block.type == 'tool_use':
                                has_tool_call = True
                                initial_input = getattr(content_block, 'input', None)
                                if initial_input is None:
                                    initial_input = {}
                                content_blocks[index] = {
                                    'type': 'tool_use',
                                    'id': content_block.id,
                                    'name': content_block.name,
                                    'input': initial_input
                                }
                            elif content_block.type == 'thinking':
                                content_blocks[index] = {
                                    'type': 'thinking',
                                    'thinking': ''
                                }
                                
                        elif event.type == 'content_block_delta':
                            # Accumulate content
                            index = event.index
                            delta = event.delta

                            block = content_blocks.get(index)
                            if not block:
                                continue

                            if delta.type == 'text_delta':
                                block.setdefault('text', '')
                                block['text'] += delta.text
                                
                                # Stream text delta to RTLayer if enabled and no tool call
                                if should_stream_to_rtlayer and not has_tool_call:
                                    stream_data = {
                                        'type': 'delta',
                                        'delta': delta.text
                                    }
                                    await send_message(cred=response_format['cred'], data={'streaming': True, 'chunk': stream_data, 'success': True})
                                    
                            elif delta.type == 'input_json_delta' and block.get('type') == 'tool_use':
                                # For tool use, we need to accumulate the JSON string
                                block.setdefault('partial_json', '')
                                block['partial_json'] += delta.partial_json
                            elif delta.type == 'input_text_delta' and block.get('type') == 'tool_use':
                                block.setdefault('partial_text', '')
                                block['partial_text'] += delta.partial_text
                            elif delta.type == 'thinking_delta':
                                block.setdefault('thinking', '')
                                block['thinking'] += delta.thinking
                                
                        elif event.type == 'content_block_stop':
                            # Finalize content block
                            index = event.index
                            if index in content_blocks:
                                block = content_blocks[index]
                                if block['type'] == 'tool_use':
                                    if 'partial_json' in block:
                                        # Parse the accumulated JSON for tool input
                                        try:
                                            if block['partial_json'] == "":
                                                block['input'] = {}
                                            else:
                                                block['input'] = json.loads(block['partial_json'])
                                        except json.JSONDecodeError:
                                            # If JSON parsing fails, keep as string
                                            block['input'] = block.get('partial_json', {})
                                        finally:
                                            del block['partial_json']  # Remove temporary field
                                    if 'partial_text' in block:
                                        existing_input = block.get('input')
                                        partial_text = block.pop('partial_text')
                                        if isinstance(existing_input, str):
                                            block['input'] = existing_input + partial_text
                                        elif existing_input in (None, {}, []):
                                            block['input'] = partial_text
                                        else:
                                            block['input'] = partial_text
                                        
                        elif event.type == 'message_delta':
                            # Update message-level information
                            delta = event.delta
                            if hasattr(delta, 'stop_reason') and delta.stop_reason:
                                accumulated_response['stop_reason'] = delta.stop_reason
                            if hasattr(delta, 'stop_sequence') and delta.stop_sequence:
                                accumulated_response['stop_sequence'] = delta.stop_sequence
                            # Update usage if present
                            if hasattr(event, 'usage') and event.usage:
                                accumulated_response['usage']['output_tokens'] = event.usage.output_tokens
                                
                        elif event.type == 'message_stop':
                            # Finalize the response
                            break
                
                # Send stream end signal if streaming was enabled and no tool call
                if should_stream_to_rtlayer and not has_tool_call:
                    await send_message(cred=response_format['cred'], data={'streaming': True, 'done': True, 'success': True})
                
                # Convert content_blocks dict to ordered list
                ordered_content = [content_blocks[i] for i in sorted(content_blocks.keys())]

                merged_content = []
                current_text_block = None

                for block in ordered_content:
                    if block.get('type') == 'text':
                        if current_text_block is None:
                            current_text_block = {
                                'type': 'text',
                                'text': block.get('text', '')
                            }
                        else:
                            current_text_block['text'] += block.get('text', '')
                    else:
                        if current_text_block is not None:
                            merged_content.append(current_text_block)
                            current_text_block = None
                        merged_content.append(block)

                if current_text_block is not None:
                    merged_content.append(current_text_block)

                accumulated_response['content'] = merged_content
                return {'success': True, 'response': accumulated_response}
                
            except Exception as error:
                # Send error to RTLayer if streaming was active
                if should_stream_to_rtlayer:
                    await send_message(cred=response_format['cred'], data={'streaming': True, 'error': str(error), 'success': False})
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
            message_id=None,
            org_id=None,
            alert_on_retry=False,
            name=name,
            org_name=org_name,
            service=service,
            count=count,
            token_calculator=token_calculator
        )

    except Exception as e:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("Anthropic runmodel error=>", e)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
