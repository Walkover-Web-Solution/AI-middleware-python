from openai import AsyncOpenAI
import traceback
import copy
from ...utils.ai_middleware_format import send_alert
from ...utils.helper import Helper

async def runModel(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None):
    try:
        openAI = AsyncOpenAI(api_key=apiKey)

        # Function to execute the API call
        async def api_call(config):
            try:
                chat_completion = await openAI.chat.completions.create(**config)
                return {'success': True, 'response': chat_completion.to_dict()}
            except Exception as error:
                return {'success': False, 'error': str(error), 'status_code': error.status_code if hasattr(error, 'status_code') else None}

        # Start timer
        timer.start()

        # Start the first API call
        first_config = copy.deepcopy(configuration)
        first_result = await api_call(first_config)

        if first_result['success']:
            if not Helper.check_space_issue(first_result):
                execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
                print("First API call completed successfully.")
                return first_result
        else:
            print("First API call failed with error:", first_result['error'])
            traceback.print_exc()
            if Helper.check_error_status_code(first_result['status_code']):
                return first_result

            # Retry with a different model
            await send_alert(data={"configuration": configuration, "message_id": message_id, "bridge_id": bridge_id, "org_id": org_id, "message": "retry mechanism started due to error"})
            second_config = copy.deepcopy(configuration)
            second_config['model'] = 'o1-preview' if configuration['model'] == 'o1-preview' else ('gpt-4o-2024-08-06' if configuration['model'] == 'gpt-4o' else 'gpt-4o')
            second_result = await api_call(second_config)

            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
            if second_result['success']:
                print("Second API call completed successfully.")
                return second_result
            else:
                print("Second API call failed with error:", second_result['error'])
                traceback.print_exc()
                return second_result

    except Exception as error:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
    