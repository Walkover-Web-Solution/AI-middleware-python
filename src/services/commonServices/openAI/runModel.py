from .openAIInitializerService import OpenAIInitializer
import traceback
import json

async def runModel(configuration, chat=True, apiKey=None):
    try:
        OpenAIConfig = OpenAIInitializer(apiKey)
        openAI = OpenAIConfig.getOpenAIService()
        if chat:
            chat_completion = openAI.chat.completions.create(**configuration)
            response = chat_completion.to_dict()
            return {
                'success': True,
                'response': response
            }
        response = await openAI.completions.create(**configuration)
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
