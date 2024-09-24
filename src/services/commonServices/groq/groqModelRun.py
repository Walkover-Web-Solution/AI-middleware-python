import traceback
import json
from groq import Groq
from ...utils.log import execution_time_logs
from ...utils.time import Timer

async def groq_runmodel(configuration, apiKey, execution_time_logs):
    try:
        timer = Timer()
        Groq_config = Groq(api_key = apiKey)
        timer.start()
        chat_completion = Groq_config.chat.completions.create(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Groq chat completion")
        response = chat_completion.to_dict()
        return {
            'success': True,
            'response': response
        }
    except Exception as error:
        print("runmodel error=>", error)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Groq chat completion")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
