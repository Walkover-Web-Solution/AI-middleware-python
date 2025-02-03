import json
from .baseService.utils import sendResponse
from src.services.utils.apiservice import fetch
from src.services.commonServices.createConversations import ConversationService
import uuid

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
        response, rs_headers = await fetch(
            f"https://proxy.viasocket.com/proxy/api/1258584/29gjrmh24/api/v2/model/chat/completion",
            "POST",
            {
                "pauthkey": "1b13a7a038ce616635899a239771044c",
                "Content-Type": "application/json"
            },
            None,
            {
                "user": f'Generate suggestions based on the user conversations and user prompt. User prompt: {final_prompt} and user conversation: {conversation}',
                "bridge_id": "674710c9141fcdaeb820aeb8",
                "thread_id": parsed_data.get('thread_id') or str(uuid.uuid4()),
            }
        )
        response['response']['data'] = json.loads(response.get('response',{}).get('data',{}).get('content',""))
        await sendResponse(response_format, response.get('response'), success=True)
            
    except Exception as err:
        print("Error calling function=>", err)
    