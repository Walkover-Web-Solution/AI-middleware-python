import asyncio
import traceback
# from services.run_model import run_model
from .runModel import runModel
from ..anthrophic.antrophicModelRun import anthropic_runmodel
from ....configs.constant import service_name
from ..groq.groqChats import groq_chats

async def chats(configuration, apikey, service):
    try:
        response = {}
        if service == service_name['openai']:
            response = await runModel(configuration, True, apikey)
        elif service == service_name['anthropic']:
            response = await anthropic_runmodel(configuration, apikey)
        elif service == service_name['groq']:
            response = await groq_chats(configuration, apikey)
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
