from ..db_services import conversationDbService as chatbotDbService
import traceback

async def getAllThreads(bridge_id, org_id, page, pageSize):
    try:
        chats = await chatbotDbService.findAllThreads(bridge_id, org_id, page, pageSize)
        return { 'success': True, 'data': chats }
    except Exception as err:
        print("getAllThreads =>", err)
        return { 'success': False, 'message': str(err) }

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
        return { 'success': True, 'data': chats }
    except Exception as err:
        print("Error in getting thread:",err)
        traceback.print_exc()
        return { 'success': False, 'message': str(err) }

async def getChatData(chat_id):
    try:
        chat = await chatbotDbService.findChat(chat_id)
        return { 'success': True, 'data': chat }
    except Exception as err:
        print(err)
        return { 'success': False, 'message': str(err) }

async def getThreadHistory(thread_id, org_id, bridge_id):
    try:
        chats = await chatbotDbService.findMessage(org_id, thread_id, bridge_id)
        return { 'success': True, 'data': chats }
    except Exception as err:
        print(err)
        return { 'success': False, 'message': str(err) }

async def savehistory(thread_id, sub_thread_id, userMessage, botMessage, org_id, bridge_id, model_name, type, messageBy, userRole="user", tools={}, chatbot_message = "",tools_call_data = [],message_id = None, version_id = None, image_url = None, revised_prompt = None):
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
            'revised_prompt' : revised_prompt
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

        if botMessage:
            chatToSave.append({
                'thread_id': thread_id,
                'sub_thread_id': sub_thread_id,
                'org_id': org_id,
                'model_name': model_name,
                'message': "" if messageBy == "tool_calls" else botMessage,
                'message_by': messageBy,
                'type': type,
                'bridge_id': bridge_id,
                'function': botMessage if messageBy == "tool_calls" else {},
                'chatbot_message' : chatbot_message or "",
                'message_id' : message_id,
                'revised_prompt' : revised_prompt,
                "image_url" : image_url
            })

        # if userRole == "tool":
        #     success =  chatbotDbService.deleteLastThread(org_id, thread_id, bridge_id)
        #     chatToSave = chatToSave[-1:]
        #     if not success:
        #         return { 'success': False, 'message': "failed to delete last chat!" }

        result = chatbotDbService.createBulk(chatToSave)
        return { 'success': True, 'message': "successfully saved chat history", 'result': list(result) }
    except Exception as error:
        print("saveconversation error=>", error)
        traceback.print_exc()
        return { 'success': False, 'message': str(error) }

# Exporting the functions
__all__ = ['getAllThreads', 'savehistory', 'getThread', 'getThreadHistory', 'getChatData']
