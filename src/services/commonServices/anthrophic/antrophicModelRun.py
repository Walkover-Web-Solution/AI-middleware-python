from anthropic import AsyncAnthropic
import json
import copy
import traceback
from ...utils.helper import Helper

async def anthropic_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer):
    try:
        # async client
        antrophic_config = AsyncAnthropic(api_key=apikey)

        # Function to execute the API call
        async def api_call(config):
            try:
                Antrophic = await antrophic_config.messages.create(**config)
                return {'success': True, 'response': Antrophic.to_dict()}
            except Exception as error:
                return {'success': False, 'error': str(error), 'status_code': error.status_code if hasattr(error, 'status_code') else None}

        # Start timer
        timer.start()

        # Start the first API call
        first_config = copy.deepcopy(configuration)
        first_result = await api_call(first_config)
        print(first_result)

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
            second_config = copy.deepcopy(configuration)
            second_config['model'] = 'claude-3-5-sonnet-20241022' if configuration['model'] == 'claude-3-5-sonnet-latest' else 'claude-3-5-sonnet-latest'
            second_result = await api_call(second_config)

            execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
            if second_result['success']:
                print("Second API call completed successfully.")
                return second_result
            else:
                print("Second API call failed with error:", second_result['error'])
                traceback.print_exc()
                return second_result

    except Exception as e:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        print("Antrophic runmodel error=>", e)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }