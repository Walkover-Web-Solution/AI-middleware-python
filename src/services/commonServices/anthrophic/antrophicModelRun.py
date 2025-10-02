from anthropic import AsyncAnthropic
import traceback
from ..retry_mechanism import execute_with_retry
# from src.services.utils.unified_token_validator import validate_anthropic_token_limit
from globals import *


async def anthropic_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer, name = "", org_name = "", service = "", count = 0, token_calculator=None):
    """Invoke Anthropic messages API with retry and alternate model support."""
    try:
        # # Validate token count before making API call
        # model_name = configuration.get('model')
        # validate_anthropic_token_limit(configuration, model_name, service, apikey)
        
        # Initialize async client
        anthropic_client = AsyncAnthropic(api_key=apikey)

        # Define the API call function
        async def api_call(config):
            """Call Anthropic asynchronously and wrap result in a dict."""
            try:
                response = await anthropic_client.messages.create(**config)
                return {'success': True, 'response': response.to_dict()}
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'status_code', None)
                }

        # Define how to get the alternative configuration
        def get_alternative_config(config):
            """Toggle between default and dated Sonnet models."""
            current_model = config.get('model', '')
            if current_model == 'claude-3-5-sonnet-latest':
                config['model'] = 'claude-3-5-sonnet-20241022'
            else:
                config['model'] = 'claude-3-5-sonnet-latest'
            return config

        # Execute with retry
        return await execute_with_retry(
            configuration=configuration,
            api_call=api_call,
            get_alternative_config=get_alternative_config,
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
        
async def anthropic_test_model(configuration, api_key) : 
    """Execute a single Anthropic request for credential validation."""
    anthropic_client = AsyncAnthropic(api_key = api_key)
    try:
        response = await anthropic_client.messages.create(**configuration)
        return {'success': True, 'response': response.to_dict()}
    except Exception as error:
        return {
            'success': False,
            'error': str(error),
            'status_code': getattr(error, 'status_code', None)
        }
