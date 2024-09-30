from .openAIInitializerService import OpenAIInitializer
import traceback
import json

async def runModel(configuration, apiKey, execution_time_logs, bridge_id, timer):
    try:
        OpenAIConfig = OpenAIInitializer(apiKey)
        openAI = OpenAIConfig.getOpenAIService()
        timer.start()
        chat_completion = openAI.chat.completions.create(**configuration)
        response = chat_completion.to_dict()
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("OpenAI chat completion")
        print(11, json.dumps(configuration), 22, bridge_id)
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
