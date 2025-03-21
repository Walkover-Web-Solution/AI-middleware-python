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
        chats = await add_tool_call_data_in_history(chats)
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
                'message': "" if messageBy == "tool_calls" else botMessage,
                'message_by': messageBy,
                'type': type,
                'bridge_id': bridge_id,
                'function': botMessage if messageBy == "tool_calls" else {},
                'chatbot_message' : chatbot_message or "",
                'message_id' : message_id,
                'revised_prompt' : revised_prompt,
                "image_url" : image_url,
                'version_id': version_id,
                "annotations" : annotations
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

async def add_tool_call_data_in_history(chats):

    final_array = [None] * 6
    i = 5  # Start filling from the end
    index = 0
    length = len(chats)

    def process_tool_call(next_chat, tools_call_chat):
        tools_call_data = tools_call_chat.get('tools_call_data', [])
        messages = []
        for call_data in tools_call_data:
            call_info = next(iter(call_data.values()))
            name = call_info.get('name', '')
            messages.append(f"{name}")
        if messages:
            combined_message = "tool_call has been done function name:- " + ', '.join(messages)
            if next_chat['content']:
                next_chat['content'] += '\n' + combined_message

    # Add the first assistant at position 5
    while index < length:
        chat = chats[index]
        if chat['role'] == 'assistant':
            # Check tools_call next
            if index + 1 < length and chats[index + 1]['role'] == 'tools_call':
                process_tool_call(chat, chats[index + 1])
                index += 1  # Skip tools_call
            final_array[i] = chat
            i -= 1
            index += 1
            break
        index += 1

    # Alternate user -> assistant -> user -> assistant (reverse fill)
    expect_user = True
    while index < length and i >= 0:
        chat = chats[index]
        if expect_user and chat['role'] == 'user':
            final_array[i] = chat
            i -= 1
            expect_user = False
        elif not expect_user and chat['role'] == 'assistant':
            if index + 1 < length and chats[index + 1]['role'] == 'tools_call':
                process_tool_call(chat, chats[index + 1])
                index += 1  # Skip tools_call
            final_array[i] = chat
            i -= 1
            expect_user = True
        index += 1

    return final_array


# Exporting the functions
__all__ = ['getAllThreads', 'savehistory', 'getThread', 'getThreadHistory', 'getChatData']
