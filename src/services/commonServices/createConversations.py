import traceback
class ConversationService:
    @staticmethod
    def createOpenAiConversation(conversation):
        try:
            threads = []
            print('conversation', conversation)
            for message in conversation:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    threads.append({'role': message['role'], 'content': message['content']})
            return {
                'success': True,
                'messages': threads
            }
        except Exception as e:
            print("create conversation error=>", e)
            return {
                'success': False,
                'error': str(e),
                'messages': []
            }

    @staticmethod
    def createGeminiConversation(conversation):
        try:
            threads = []
            previous_role = "model"
            for message in conversation:
                chat = {}
                role = "model" if message['role'] != "model" else message['role']
                chat['role'] = role
                chat['parts'] = message['content']
                if previous_role != role:
                    threads.append(chat)
                previous_role = role

            if previous_role == "user":
                threads.append({
                    'role': "model",
                    'parts': ""
                })
                
            return {
                'success': True,
                'messages': threads
            }
        except Exception as e:
            print("create conversation error=>", e)
            return {
                'success': False,
                'error': str(e),
                'messages': []
            }

# Example usage:
# result = ConversationService.create_openai_conversation(conversation)
# result = ConversationService.create_gemini_conversation(conversation)
