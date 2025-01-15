
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
    alert_on_retry=False
):
    try:
        # Start timer
        timer.start()

        # Execute the first API call
        first_config = copy.deepcopy(configuration)
        first_result = await api_call(first_config)

        if first_result['success']:
            if not await check_space_issue(first_result.get('response')):
                execution_time_logs[len(execution_time_logs) + 1] = timer.stop("API chat completion")
                print("First API call completed successfully.")
                return first_result
        else:
            print("First API call failed with error:", first_result['error'])
            traceback.print_exc()
            if check_error_status_code(first_result.get('status_code')):
                return first_result

            # Send alert if required
            if alert_on_retry:
                await send_alert(data={
                    "configuration": configuration,
                    "message_id": message_id,
                    "bridge_id": bridge_id,
                    "org_id": org_id,
                    "message": "Retry mechanism started due to error"
                })

            # Generate alternative configuration
            second_config = get_alternative_config(copy.deepcopy(configuration))
            second_result = await api_call(second_config)

            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("API chat completion")
            if second_result['success']:
                print("Second API call completed successfully.")
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
    
async def check_error_status_code(error_code):
    if error_code in ['401']:
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