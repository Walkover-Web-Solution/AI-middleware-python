
import asyncio
import copy
import traceback
from ..utils.ai_middleware_format import send_alert
from src.configs.constant import service_name

async def execute_with_retry(
    configuration,
    api_call,
    get_alternative_config,
    execution_time_logs,
    timer,
    bridge_id=None,
    message_id=None,
    org_id=None,
    alert_on_retry=False,
    name = "",
    org_name= "",
    service = "",
    count = 0,
    token_calculator = None
):
    try:
        # Start timer
        firstAttemptError = {}
        timer.start()

        # Execute the first API call
        first_config = copy.deepcopy(configuration)
        first_result = await api_call(first_config)

        if first_result['success']:
            first_result['response'] = await check_space_issue(first_result['response'], service)
            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            token_calculator.calculate_usage(first_result['response'])
            return first_result
        else:
            print("First API call failed with error:", first_result['error'])
            traceback.print_exc()
            firstAttemptError = first_result['error']
            if check_error_status_code(first_result.get('status_code')):
                return first_result

            # Send alert if required
            if alert_on_retry:
                await send_alert(data={
                    "org_name" : org_name,
                    "bridge_name" : name,
                    "configuration": configuration,
                    "message_id": message_id,
                    "bridge_id": bridge_id,
                    "org_id": org_id,
                    "message": "Retry mechanism started due to error",
                    "error" : first_result.get('error')
                })

            # Generate alternative configuration
            second_config = get_alternative_config(copy.deepcopy(configuration))
            filter_model_keys(second_config)
            second_result = await api_call(second_config)

            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            if second_result['success']:
                token_calculator.calculate_usage(second_result['response'])
                second_result['response'] = await check_space_issue(second_result['response'], service)
                print("Second API call completed successfully.")
                second_result['response']['firstAttemptError'] = firstAttemptError
                second_result['response']['fallback'] = True
                second_result['response']['fallback_model'] = second_config['model']
                second_result['response']['model'] = second_config['model']
                return second_result
            else:
                print("Second API call failed with error:", second_result['error'])
                traceback.print_exc()
                if 'response' not in second_result:
                    second_result['response'] = {}
                second_result['response']['fallback_model'] = second_config['model']
                second_result['response']['model'] = second_config['model']
                return second_result

    except Exception as e:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        print("execute_with_retry error=>", e)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }
    
def check_error_status_code(error_code):
    if error_code in [401,404,429]:
        return True
    return False

async def check_space_issue(response, service=None):
    
    
    content = None
    if service == service_name['openai_completion'] or service == service_name['groq'] or service == service_name['open_router'] or service == service_name['mistral'] or service == service_name['gemini'] or service == service_name['ai_ml']:
        content = response.get("choices", [{}])[0].get("message", {}).get("content", None)
    elif service == service_name['anthropic']:
        # Handle empty content array
        content_list = response.get("content", [])
        if content_list:
            # Iterate through content blocks to find the first "text" type block
            for content_block in content_list:
                if isinstance(content_block, dict) and content_block.get("type") == "text":
                    content = content_block.get("text", None)
                    break
        else:
            content = None
    elif service == service_name['openai']:
        output_list = response.get("output", [])
        if output_list:
            first_output = output_list[0]
            if first_output.get("type") == "function_call":
                content_list = first_output.get("content", [])
                content = content_list[0].get("text", None) if content_list else None
            else:
                # Find first message type item
                for item in output_list:
                    if item.get("type") == "message":
                        content_list = item.get("content", [])
                        content = content_list[0].get("text", None) if content_list else None
                        break
        else:
            content = None
    
    if content is None:
        return response
        
    parsed_data = content.replace(" ", "").replace("\n", "")
    
    if parsed_data == '' and content:
        response['alert_flag'] = True
        text = 'AI is Hallucinating and sending \'\n\' please check your prompt and configurations once'
        if service == service_name['openai_completion'] or service == service_name['groq'] or service == service_name['open_router'] or service == service_name['mistral'] or service == service_name['gemini'] or service == service_name['ai_ml']:
            response["choices"][0]["message"]["content"] = text
        elif service == service_name['anthropic']:
            # Handle empty content array for anthropic
            content_list = response.get("content", [])
            if content_list:
                # Find the first text block and update it
                for i, content_block in enumerate(content_list):
                    if isinstance(content_block, dict) and content_block.get("type") == "text":
                        response["content"][i]["text"] = text
                        break
                else:
                    # If no text block found, create one
                    response["content"].append({"type": "text", "text": text})
            else:
                # If content array is empty, create it with a text block
                response["content"] = [{"type": "text", "text": text}]
        elif service == service_name['openai']:
            output_list = response.get("output", [])
            if output_list:
                first_output = output_list[0]
                if first_output.get("type") == "function_call":
                    content_list = first_output.get("content", [])
                    if content_list:
                        response["output"][0]["content"][0]["text"] = text
                    else:
                        response["output"][0]["content"] = [{"text": text}]
                else:
                    # Find first message type item and update it
                    for i, item in enumerate(output_list):
                        if item.get("type") == "message":
                            content_list = item.get("content", [])
                            if content_list:
                                response["output"][i]["content"][0]["text"] = text
                            else:
                                response["output"][i]["content"] = [{"text": text}]
                            break
    return response

def filter_model_keys(config): # to be opmized
    if config['model'] == 'o1':
        keys_to_remove = ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'logprobs', 'echo', 'topK', 'n', 'stopSequences', 'best_of', 'suffix', 'parallel_tool_calls']
        for key in keys_to_remove:
            if key in config:
                del config[key]