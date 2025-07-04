from mistralai import Mistral
from mistralai.models import UserMessage
import traceback
from ..retry_mechanism import execute_with_retry
from globals import *


async def mistral_model_run(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name = "", org_name= "", service = "", count=0):
    try:
        mistral = Mistral(api_key=apiKey)

        # Define the API call function
        async def api_call(config):
            try:
                chat_completion = await mistral.chat.complete_async(**config)
                return {'success': True, 'response': chat_completion.model_dump()}
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'status_code', None)
                }

        # Define how to get the alternative configuration
        def get_alternative_config(config):
            current_model = config.get('model', '')
            if current_model == 'mistral-small-2506':
                config['model'] = 'magistral-small-2506'
            elif current_model == 'magistral-small-2506':
                config['model'] = 'mistral-small-2506'
            else:
                config['model'] = 'magistral-small-2506'
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
            org_name = org_name,
            service = service,
            count = count
        )

    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }