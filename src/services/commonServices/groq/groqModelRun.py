from groq import AsyncGroq
import traceback
from ..retry_mechanism import execute_with_retry
from globals import *

async def groq_runmodel(configuration, apiKey, execution_time_logs, bridge_id, timer, name = "", org_name = "", service = "", count = 0, token_calculator=None):
    try:
        # Initialize async client
        groq_client = AsyncGroq(api_key=apiKey)

        # Define the API call function
        async def api_call(config):
            try:
                response = await groq_client.chat.completions.create(**config)
                return {'success': True, 'response': response.to_dict()}
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'status_code', None)
                }

        # Define how to get the alternative configuration
        def get_alternative_config(config):
            current_model = config.get('model', '')
            if current_model == 'llama3-8b-8192':
                config['model'] = 'llama3-70b-8192'
            else:
                config['model'] = 'llama3-8b-8192'
            return config

        # Execute with retry
        return await execute_with_retry(
            configuration = configuration,
            api_call= api_call,
            get_alternative_config = get_alternative_config,
            execution_time_logs=execution_time_logs,
            timer = timer,
            bridge_id = bridge_id,
            message_id= None,
            org_id = None,
            alert_on_retry= False,
            name = name,
            org_name = org_name ,
            service = service,
            count = count,
            token_calculator = token_calculator
        )

    except Exception as e:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("Groq runmodel error=>", e)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

async def groq_test_model(configuration, api_key): 
    groq_client = AsyncGroq(api_key = api_key)
    try:
        response = await groq_client.chat.completions.create(**configuration)
        return {'success': True, 'response': response.to_dict()}
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'status_code': getattr(error, 'status_code', None)
        }