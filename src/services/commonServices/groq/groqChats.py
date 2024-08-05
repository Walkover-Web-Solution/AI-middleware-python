import traceback
from .groqModelRun import groq_runmodel

async def groq_chats(configuration, apikey):
    try:
        response = await groq_runmodel(configuration, True, apikey)
        if not response['success']:
            return {
                'success': False,
                'error': response['error']
            }
        return {
            'success': True,
            'response': response['response']
        }
    except Exception as e:
        traceback.print_exc()
        print("chats error=>", e)
        return {
            'success': False,
            'error': str(e)
        }

# Exporting chats function
__all__ = ["chats"]
