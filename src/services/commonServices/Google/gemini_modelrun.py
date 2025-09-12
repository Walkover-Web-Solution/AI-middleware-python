from openai import AsyncOpenAI
import traceback
from ..retry_mechanism import check_space_issue
# from src.services.utils.unified_token_validator import validate_gemini_token_limit
from globals import *


async def gemini_modelrun(configuration, apiKey, execution_time_logs, bridge_id, timer, message_id=None, org_id=None, name = "", org_name= "", service = "", count=0, token_calculator=None):
    try:
        # Validate token count before making API call
        # model_name = configuration.get('model')
        # validate_gemini_token_limit(configuration, model_name, service, apiKey)
        
        gemini = AsyncOpenAI(api_key=apiKey, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
        
        # Start timer
        timer.start()
        
        try:
            chat_completion = await gemini.chat.completions.create(**configuration)
            result = {'success': True, 'response': chat_completion.to_dict()}
            
            # Apply space issue check
            result['response'] = await check_space_issue(result['response'], service)
            
            # Calculate usage and log execution time
            token_calculator.calculate_usage(result['response'])
            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            
            return result
            
        except Exception as api_error:
            execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
            traceback.print_exc()
            return {
                'success': False,
                'error': str(api_error),
                'status_code': getattr(api_error, 'status_code', None)
            }

    except Exception as error:
        execution_time_logs.append({"step": f"{service} Processing time for call :- {count + 1}", "time_taken": timer.stop("API chat completion")})
        logger.error("runModel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }