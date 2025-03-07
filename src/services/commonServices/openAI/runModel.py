from openai import AsyncOpenAI
import traceback
from ..retry_mechanism import execute_with_retry


async def runModel(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name = "", org_name= ""):
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

        # Define how to get the alternative configuration
        def get_alternative_config(config):
            current_model = config.get('model', '')
            if current_model == 'o1':
                config['model'] = 'gpt-4o-2024-08-06'
            elif current_model == 'gpt-4o':
                config['model'] = 'o1'
            else:
                config['model'] = 'gpt-4o'
            return config

        # Execute with retry
        return await execute_with_retry(
            configuration=configuration,
            api_call=api_call,
            get_alternative_config=get_alternative_config,
            execution_time_logs=execution_time_logs,
            timer=timer,
            bridge_id=bridge_id,
            message_id=message_id,
            org_id=org_id,
            alert_on_retry=True,
            name = name,
            org_name = org_name
        )

    except Exception as error:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        print("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }

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