from .openAIInitializerService import OpenAIInitializer
import traceback
import json
import time
from ...utils.time import Timer
from ...utils.log import execution_times_log

async def runModel(configuration, chat=True, apiKey=None, run_id = 0):
    timer = Timer()
    try:
        OpenAIConfig = OpenAIInitializer(apiKey)
        openAI = OpenAIConfig.getOpenAIService()
        timer.start()
        if chat:
            chat_completion = openAI.chat.completions.create(**configuration)
            response = chat_completion.to_dict()
            time_taken = timer.stop("OpenAI chat completion")
            execution_times_log[run_id] = time_taken
            return {
                'success': True,
                'response': response
            }
        response = await openAI.completions.create(**configuration)
        time_taken = timer.stop("OpenAI completion")
        return {
            'success': True,
            'response': response
        }
    except Exception as error:


        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
