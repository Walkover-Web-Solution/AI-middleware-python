import traceback
import json
from openai import OpenAI

async def OpenAIImageModel(configuration, apiKey, execution_time_logs, timer):
    try:
        del configuration['response_format']
        openai_config = OpenAI(api_key = apiKey)
        timer.start()
        chat_completion = openai_config.images.generate(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        response = chat_completion.to_dict()
        return {
            'success': True,
            'response': response
        }
    except Exception as error:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Antrophic chat completion")
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
