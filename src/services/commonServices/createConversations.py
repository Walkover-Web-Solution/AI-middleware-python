import traceback
from fastapi import HTTPException
class ConversationService:
    @staticmethod
    def createOpenAiConversation(conversation):
        try:
            threads = []
            for message in conversation or []:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    threads.append({'role': message['role'], 'content': message['content']})
            
            return {
                'success': True,
                'messages': threads
            }
        except Exception as e:
            traceback.print_exc()
            print("create conversation error=>", e)
            raise ValueError(e.args[0])

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

    @staticmethod
    def createAnthropicConversation(conversation):
        try:
            if conversation == None:
                conversation = []
            threads = []
            expected_role = 'user'

            for i, message in enumerate(conversation):
                if message['role'] not in ['assistant', 'user']:
                    raise ValueError(f"Invalid role '{message['role']}' at index {i}. Allowed roles are 'assistant' and 'user'.")
                if message['role'] != expected_role:
                    raise ValueError(f"Conversation format is not correct at index {i}. Expected role: {expected_role}")
                
                threads.append({
                    'role': message['role'], 
                    'content': [{"type": "text", "text": message['content']}]
                })
                expected_role = 'user' if expected_role == 'assistant' else 'assistant'
            if len(threads) % 2 != 0:
                raise ValueError("Conversation format is not correct. Mismatched number of 'assistant' and 'user' messages.")

            return {
                'success': True,
                'messages': threads
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print("create conversation error=>", e)
            raise HTTPException(status_code=500, detail="Internal Server Error")
# Example usage:
# result = ConversationService.create_openai_conversation(conversation)
# result = ConversationService.create_gemini_conversation(conversation)
