import traceback
import json
from groq import Groq

async def groq_runmodel(configuration, chat=True, apiKey=None):
    try:
        Groq_config = Groq(api_key = apiKey)
        if chat:
            chat_completion = Groq_config.chat.completions.create(**configuration)
            response = chat_completion.to_dict()
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
