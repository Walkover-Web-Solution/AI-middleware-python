from anthropic import AsyncAnthropic
import traceback
import json
from ..api_executor import execute_api_call
# from src.services.utils.unified_token_validator import validate_anthropic_token_limit
from globals import *


async def anthropic_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer, name = "", org_name = "", service = "", count = 0, token_calculator=None):
    try:
        # # Validate token count before making API call
        # model_name = configuration.get('model')
        # validate_anthropic_token_limit(configuration, model_name, service, apikey)
        
        # Initialize async client
        anthropic_client = AsyncAnthropic(api_key=apikey)

        # Define the API call function with streaming
        async def api_call(config):
            try:
                # Log the configuration for debugging
                logger.info(f"Anthropic API call config: {config}")
                
                # Remove 'stream' parameter if present as it's not needed for the stream method
                config_copy = config.copy()
                if 'stream' in config_copy:
                    del config_copy['stream']
                
                # Check if streaming is disabled for debugging
                if config.get('stream') == False:
                    # Non-streaming call for debugging
                    response = await anthropic_client.messages.create(**config_copy)
                    return {'success': True, 'response': response.to_dict()}
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
                async with anthropic_client.messages.stream(**config_copy) as stream:
                    async for event in stream:
                        logger.debug(f"Received event type: {event.type}")
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
                                content_blocks[index] = {
                                    'type': 'tool_use',
                                    'id': content_block.id,
                                    'name': content_block.name,
                                    'input': {}
                                }
                            elif content_block.type == 'server_tool_use':
                                content_blocks[index] = {
                                    'type': 'server_tool_use',
                                    'id': content_block.id,
                                    'name': content_block.name,
                                    'input': getattr(content_block, 'input', {})
                                }
                            elif content_block.type == 'thinking':
                                content_blocks[index] = {
                                    'type': 'thinking',
                                    'thinking': ''
                                }
                            elif content_block.type == 'web_search_tool_result':
                                content_blocks[index] = {
                                    'type': 'web_search_tool_result',
                                    'tool_use_id': getattr(content_block, 'tool_use_id', ''),
                                    'content': getattr(content_block, 'content', [])
                                }
                            else:
                                # Handle any other content types generically
                                content_blocks[index] = {
                                    'type': content_block.type,
                                    **{attr: getattr(content_block, attr, None) for attr in dir(content_block) if not attr.startswith('_') and attr != 'type'}
                                }
                                
                        elif event.type == 'content_block_delta':
                            # Accumulate content
                            index = event.index
                            delta = event.delta
                            
                            if delta.type == 'text_delta':
                                if 'text' in content_blocks[index]:
                                    content_blocks[index]['text'] += delta.text
                            elif delta.type == 'input_json_delta':
                                # For tool use, we need to accumulate the JSON string
                                if 'partial_json' not in content_blocks[index]:
                                    content_blocks[index]['partial_json'] = ''
                                content_blocks[index]['partial_json'] += delta.partial_json
                            elif delta.type == 'thinking_delta':
                                if 'thinking' in content_blocks[index]:
                                    content_blocks[index]['thinking'] += delta.thinking
                            # Handle other delta types generically
                            else:
                                # For server-side tools and other content types, they usually don't have deltas
                                # as they are provided complete in the content_block_start event
                                pass
                                
                        elif event.type == 'content_block_stop':
                            # Finalize content block
                            index = event.index
                            if index in content_blocks:
                                block = content_blocks[index]
                                if block['type'] == 'tool_use' and 'partial_json' in block:
                                    # Parse the accumulated JSON for tool input
                                    try:
                                        block['input'] = json.loads(block['partial_json'])
                                        del block['partial_json']  # Remove temporary field
                                    except json.JSONDecodeError:
                                        # If JSON parsing fails, keep as string
                                        block['input'] = block.get('partial_json', {})
                                        
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
                
                # Convert content_blocks dict to ordered list and merge consecutive text blocks
                content_list = [content_blocks[i] for i in sorted(content_blocks.keys())]
                
                # Merge consecutive text blocks
                merged_content = []
                current_text = ""
                
                for block in content_list:
                    if block['type'] == 'text':
                        # Accumulate text content
                        current_text += block.get('text', '')
                    else:
                        # If we have accumulated text, add it as a single block
                        if current_text:
                            merged_content.append({
                                'type': 'text',
                                'text': current_text
                            })
                            current_text = ""
                        
                        # Add the non-text block
                        merged_content.append(block)
                
                # Don't forget to add any remaining text at the end
                if current_text:
                    merged_content.append({
                        'type': 'text',
                        'text': current_text
                    })
                
                accumulated_response['content'] = merged_content
                print("accumulated_response", accumulated_response)
                return {'success': True, 'response': accumulated_response}
                
            except Exception as error:
                error_msg = f"Anthropic API call error: {str(error)}"
                logger.error(error_msg)
                logger.error(f"Error type: {type(error)}")
                logger.error(f"Error attributes: {dir(error)}")
                traceback.print_exc()
                
                # Try to get more detailed error information
                error_details = {
                    'error_type': str(type(error)),
                    'error_message': str(error),
                    'status_code': getattr(error, 'status_code', None),
                    'response': getattr(error, 'response', None),
                    'body': getattr(error, 'body', None)
                }
                
                return {
                    'success': False,
                    'error': str(error),
                    'error_details': error_details,
                    'status_code': getattr(error, 'status_code', None)
                }

        # Execute API call with monitoring
        return await execute_api_call(
            configuration=configuration,
            api_call=api_call,
            execution_time_logs=execution_time_logs,
            timer=timer,
            bridge_id=bridge_id,
            message_id=None,  # Adjust if needed
            org_id=None,      # Adjust if needed
            alert_on_retry=False,  # Adjust if needed
            name=name,
            org_name=org_name,
            service = service,
            count = count,
            token_calculator = token_calculator
        )

    except Exception as e:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("Anthropic runmodel error=>", e)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
    """
    Simple debug function to test Anthropic API without streaming
    """
    try:
        anthropic_client = AsyncAnthropic(api_key=api_key)
        
        # Clean configuration
        config_copy = configuration.copy()
        if 'stream' in config_copy:
            del config_copy['stream']
        
        logger.info(f"Testing Anthropic API with config: {config_copy}")
        
        # Test non-streaming first
        response = await anthropic_client.messages.create(**config_copy)
        logger.info("Non-streaming call successful")
        
        # Test streaming
        logger.info("Testing streaming...")
        async with anthropic_client.messages.stream(**config_copy) as stream:
            async for event in stream:
                logger.info(f"Stream event: {event.type}")
                if event.type == 'message_stop':
                    break
        
        logger.info("Streaming call successful")
        return {'success': True, 'message': 'Both streaming and non-streaming work'}
        
    except Exception as error:
        logger.error(f"Debug test error: {str(error)}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error),
            'status_code': getattr(error, 'status_code', None)
        }