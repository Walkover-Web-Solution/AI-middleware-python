import json
from .baseService.utils import sendResponse
from src.services.commonServices.createConversations import ConversationService
import uuid
from ..utils.ai_call_util import call_ai_middleware
from src.configs.constant import bridge_ids
from globals import *

async def chatbot_suggestions(response_format, assistant, parsed_data, params):
    try:
        user = parsed_data.get('user')
        prompt_summary = parsed_data.get('bridge_summary')
        prompt = params['configuration']['prompt']
        conversation = ConversationService.createOpenAiConversation(params.get('configuration',{}).get('conversation',{}), None).get('messages', [])
        if conversation is None:
            conversation = []
        conversation.extend([{"role": "user", "content": user}, {"role": "assistant", "content": assistant.get('data', '').get('content')}])
        final_prompt = prompt_summary if prompt_summary is not None else prompt
        random_id = str(uuid.uuid4())
        message = f'Generate suggestions based on the user conversations. \n **User Conversations**: {conversation[-2:]}'
        variables = {'prompt_summary': final_prompt}
        thread_id = f"{parsed_data.get('thread_id') or random_id}-{parsed_data.get('sub_thread_id') or random_id}"
        response = await call_ai_middleware(message, bridge_id = bridge_ids['chatbot_suggestions'], variables = variables, thread_id = thread_id)
        if 'response' not in response:
            response['response'] = {}
            response['response']['data'] = response
        await sendResponse(response_format, response.get('response'), success=True)
            
    except Exception as err:
        logger.error(f'Error calling function=>, {str(err)}')
    