import traceback
import json
from groq import Groq

async def groq_runmodel(configuration, apiKey, execution_time_logs, bridge_id, timer):
    try:
        Groq_config = Groq(api_key = apiKey)
        timer.start()
        chat_completion = Groq_config.chat.completions.create(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Groq chat completion")
        response = chat_completion.to_dict()
        print(11, json.dumps(configuration), 22, bridge_id)
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
