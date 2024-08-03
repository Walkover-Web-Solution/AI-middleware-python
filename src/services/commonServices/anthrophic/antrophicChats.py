import asyncio
import traceback
# from services.run_model import run_model
from .antrophicModelRun import anthropic_runmodel


async def chats(configuration, apikey):
    try:
        response = await anthropic_runmodel(configuration, apikey)
        if not response['success']:
            return {
                'success': False,
                'error': response['error']
            }
        return {
            'success': True,
            'modelResponse': response['response']
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
