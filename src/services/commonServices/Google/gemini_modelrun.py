import google.generativeai as genai
from google.generativeai import types
import traceback
from ..api_executor import execute_api_call
from globals import *

async def gemini_modelrun(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name = "", org_name= "", service = "", count=0, token_calculator=None):
    try:
        # Configure the Generative AI client
        genai.configure(api_key=apiKey)
        
        # Extract model name
        model_name = configuration.get('model', 'gemini-1.5-flash')
        
        # Define the API call function
        async def api_call(config):
            try:
                # Extract parameters
                temperature = config.get('temperature', 0.7)
                max_tokens = config.get('max_tokens')
                top_p = config.get('top_p')
                
                # Contents and system_instruction are now prepared in geminiCall.py
                system_instruction = config.get('system_instruction')
                contents = config.get('contents', [])
                
                # Initialize model
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                
                generation_config = types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                    top_p=top_p
                )

                # Make the async API call
                response = await model.generate_content_async(
                    contents,
                    generation_config=generation_config
                )
                
                # Return native response dict
                # The execute_api_call expect 'response' key
                return {'success': True, 'response': response.to_dict()}
                
            except Exception as error:
                return {
                    'success': False,
                    'error': str(error),
                    'status_code': getattr(error, 'code', None) # Google limits might have 'code'
                }

        # Execute API call with monitoring
        return await execute_api_call(
            configuration=configuration,
            api_call=api_call,
            execution_time_logs=execution_time_logs,
            timer=timer,
            bridge_id=bridge_id,
            message_id=message_id,
            org_id=org_id,
            alert_on_retry=True,
            name = name,
            org_name = org_name,
            service = service,
            count = count,
            token_calculator = token_calculator
        )

    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }