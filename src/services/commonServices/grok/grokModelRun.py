from openai import AsyncOpenAI
import traceback
from ..retry_mechanism import execute_with_retry
from globals import *


async def grok_model_run(
    configuration,
    api_key,
    execution_time_logs,
    bridge_id,
    timer,
    message_id,
    org_id,
    name="",
    org_name="",
    service="",
    count=0,
    token_calculator=None
):
    try:
        client = AsyncOpenAI(base_url="https://api.x.ai/v1", api_key=api_key)

        async def api_call(config):
            try:
                response = await client.chat.completions.create(**config)
                return {'success': True, 'response': response.to_dict()}
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'status_code', None)
                }

        def get_alternative_config(config):
            current_model = config.get('model', '')
            match current_model:
                case 'grok-beta':
                    config['model'] = 'grok-2-latest'
                case 'grok-2-latest':
                    config['model'] = 'grok-beta'
                case _:
                    config['model'] = 'grok-2-latest'
            return config

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
            name=name,
            org_name=org_name,
            service=service,
            count=count,
            token_calculator=token_calculator
        )

    except Exception as error:
        execution_time_logs.append({
            "step": f"{service} Processing time for call :- {count + 1}",
            "time_taken": timer.stop("API chat completion")
        })
        logger.error("grok_model_run error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }


async def grok_test_model(configuration, api_key):
    client = AsyncOpenAI(base_url="https://api.x.ai/v1", api_key=api_key)
    try:
        response = await client.chat.completions.create(**configuration)
        return {'success': True, 'response': response.to_dict()}
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'status_code': getattr(error, 'status_code', None)
        }
