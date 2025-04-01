
import copy
import traceback
from ..utils.ai_middleware_format import send_alert

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
    org_name= ""
):
    try:
        # Start timer
        firstAttemptError = {}
        timer.start()

        # Execute the first API call
        first_config = copy.deepcopy(configuration)
        first_result = await api_call(first_config)

        if first_result['success']:
            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("API chat completion")
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

            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("API chat completion")
            if second_result['success']:
                print("Second API call completed successfully.")
                second_result['response']['firstAttemptError'] = firstAttemptError
                return second_result
            else:
                print("Second API call failed with error:", second_result['error'])
                traceback.print_exc()
                return second_result

    except Exception as e:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("API chat completion")
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

async def check_space_issue(response):
    content = response.get("choices", [{}])[0].get("message", {}).get("content", None)
    if content is None:
        return False
    parsed_data = content.replace(" ", "").replace("\n", "")
    if(parsed_data == '' and content):
        return True
    return False

def filter_model_keys(config):
    if config['model'] == 'o1':
        keys_to_remove = ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty', 'logprobs', 'echo', 'topK', 'n', 'stopSequences', 'best_of', 'suffix', 'parallel_tool_calls']
        for key in keys_to_remove:
            if key in config:
                del config[key]