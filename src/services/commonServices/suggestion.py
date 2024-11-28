import json
from groq import Groq
import traceback
from .baseService.utils import sendResponse
from ..commonServices.createConversations import ConversationService
from ..utils.ai_middleware_format import Response_formatter
from config import Config
from src.services.utils.apiservice import fetch

async def chatbot_suggestions(response_format, assistant, user_msg):
    try:
        conversations = [{"role": "user", "content": user_msg}, {"role": "assistant", "content": assistant.get('data', '').get('content')}]
        
        response, rs_headers = await fetch(f"https://flow.sokt.io/func/scriGER0MdPR","POST", None,None, { "conversations": conversations})
        if response.get('success') == False:
            raise Exception(response.get('message'))
        else:
            response['response']['data']['suggestion'] = json.loads(response.get('response',{}).get('data',{}).get('content',""))
            await sendResponse(response_format, response.get('response'), success=True)
            return 
            
    except Exception as err:
        print("Error calling function=>", err)
    