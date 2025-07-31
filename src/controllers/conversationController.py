import copy
import datetime
from config import Config
from ..db_services import conversationDbService as chatbotDbService
import traceback
from globals import *
from ..configs.constant import bridge_ids
from ..services.utils.ai_call_util import call_ai_middleware
from ..db_services.ConfigurationServices import save_sub_thread_id
from ..services.commonServices.baseService.utils import sendResponse



async def getThread(thread_id, sub_thread_id, org_id, bridge_id, bridgeType):
    try:
        chats = await chatbotDbService.find(org_id, thread_id, sub_thread_id, bridge_id)
        if bridgeType:
            filtered_chats = []
            for chat in chats:
                if chat['is_reset']:
                    filtered_chats = []
                else:
                    filtered_chats.append(chat)
            chats = filtered_chats
        chats = await add_tool_call_data_in_history(chats)
        return chats
    except Exception as err:
        logger.error(f"Error in getting thread:, {str(err)}, {traceback.format_exc()}")
        raise err

async def savehistory(thread_id, sub_thread_id, userMessage, botMessage, org_id, bridge_id, model_name, type, messageBy, userRole="user", tools={}, chatbot_message = "",tools_call_data = [],message_id = None, version_id = None, image_url = None, revised_prompt = None, urls = None, AiConfig = None, annotations = None):
    try:
        chatToSave = [{
            'thread_id': thread_id,
            'sub_thread_id': sub_thread_id,
            'org_id': org_id,
            'model_name': model_name,
            'message': userMessage or "",
            'message_by': userRole,
            'type': type,
            'bridge_id': bridge_id,
            'message_id' : message_id,
            'version_id': version_id,
            'revised_prompt' : revised_prompt,
            'urls' : urls,
            'AiConfig' : AiConfig
        }]
        
        if tools:
            chatToSave.append({
                'thread_id': thread_id,
                'sub_thread_id': sub_thread_id,
                'org_id': org_id,
                'model_name': model_name,
                'message': "",
                'message_by': "tools_call",
                'type': type,
                'bridge_id': bridge_id,
                'function': tools,
                'tools_call_data': tools_call_data,
                'message_id' : message_id,
                'version_id': version_id
            })

        if botMessage is not None:
            chatToSave.append({
                'thread_id': thread_id,
                'sub_thread_id': sub_thread_id,
                'org_id': org_id,
                'model_name': model_name,
                'message': botMessage or "",
                'message_by': messageBy,
                'type': type,
                'bridge_id': bridge_id,
                'function': botMessage if messageBy == "tool_calls" else {},
                'chatbot_message' : chatbot_message or "",
                'message_id' : message_id,
                'revised_prompt' : revised_prompt,
                "image_urls" : image_url,
                'version_id': version_id,
                "annotations" : annotations
            })
        # sending data through rt layer
        chatbotSaveCopy = copy.deepcopy(chatToSave)
        for item in chatbotSaveCopy:
            item["role"] = item.pop("message_by")
            item["content"] = item.pop("message")
            if item.get('created_at') is None:
                item['created_at'] = str(datetime.datetime.now())
            if item.get('createdAt') is None:
                item['createdAt'] = str(datetime.datetime.now())

        response_format_copy = {
            'cred' : {
                'channel': org_id + bridge_id,
                'apikey': Config.RTLAYER_AUTH,
                'ttl': '1'
            },
            'type' : 'RTLayer'
        }
        dataToSend={
            'Thread':{
                "thread_id" : thread_id,
                "sub_thread_id": sub_thread_id,
                "bridge_id":bridge_id
            },
            "Messages":chatbotSaveCopy
        }
        await sendResponse(response_format_copy, dataToSend, True)

        result = chatbotDbService.createBulk(chatToSave)
        return list(result)
    except Exception as error:
        logger.error(f"saveconversation error=>, {str(error)}, {traceback.format_exc()}")
        raise error

async def add_tool_call_data_in_history(chats):
        tools_call_indices = []
    
        for i in range(len(chats)):
            current_chat = chats[i]
            if current_chat['role'] == 'tools_call':
                if i > 0 and (i + 1) < len(chats):
                    prev_chat = chats[i - 1]
                    next_chat = chats[i + 1]
                    if prev_chat['role'] == 'user' and next_chat['role'] == 'assistant':
                        tools_call_data = current_chat.get('tools_call_data', [])
                        messages = []
                        for call_data in tools_call_data:
                            call_info = next(iter(call_data.values()))
                            name = call_info.get('name', '')
                            messages.append(f"{name}")
                        if messages:
                            combined_message = "tool_call has been done function name:-  " +  ', '.join(messages)
                            if next_chat['content']:
                                next_chat['content'] += '\n' + combined_message
                        tools_call_indices.append(i)
        
        processed_chats = [chat for idx, chat in enumerate(chats) if idx not in tools_call_indices]
        return processed_chats

async def save_sub_thread_id_and_name(thread_id, sub_thread_id, org_id, thread_flag, response_format, bridge_id, user):
    try:
        if not thread_flag:
            return
        variables = {
            'user' : user
        }
        display_name = sub_thread_id
        message  = 'generate description'
        display_name = await call_ai_middleware(message, bridge_ids['generate_description'], response_type='text', variables=variables)
        await save_sub_thread_id(org_id, thread_id, sub_thread_id, display_name, bridge_id)
        if display_name is not None and display_name != sub_thread_id:
            response = {
                'data': {
                    'display_name': display_name,
                    'sub_thread_id': sub_thread_id,
                    'thread_id': thread_id,
                    'bridge_id': bridge_id
                }
            }
            await sendResponse(response_format, response, True)

    except Exception as err:
        logger.error(f"Error in saving sub thread id and name:, {str(err)}")
        return { 'success': False, 'message': str(err) }
# Exporting the functions
__all__ = ['getAllThreads', 'savehistory', 'getThread', 'getThreadHistory', 'getChatData']
