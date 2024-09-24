from .openAIInitializerService import OpenAIInitializer
import traceback
import json
import time
from ...utils.time import Timer
from ...utils.log import execution_time_logs

async def runModel(configuration, apiKey=None, run_id = 0):
    try:
        timer = Timer()
        OpenAIConfig = OpenAIInitializer(apiKey)
        openAI = OpenAIConfig.getOpenAIService()
        timer.start()
        chat_completion = openAI.chat.completions.create(**configuration)
        response = chat_completion.to_dict()
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        
        return {
            'success': True,
            'response': response
        }
    except Exception as error:

        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
