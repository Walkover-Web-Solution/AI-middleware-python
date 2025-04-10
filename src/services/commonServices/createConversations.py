import traceback
from fastapi import HTTPException
from ..utils.apiservice import fetch_images_b64
class ConversationService:
    @staticmethod
    def createOpenAiConversation(conversation, memory):
        try:
            threads = []
            if memory is not None:
                threads.append({'role': 'user', 'content': 'provide the summary of the previous conversation stored in the memory?'})
                threads.append({'role': 'assistant', 'content': f'Summary of previous conversations :  {memory}' })
            for message in conversation or []:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    content = [{"type": "text", "text": message['content']}]
                    if 'urls' in message and isinstance(message['urls'], list):
                        for url in message['urls']:
                            content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": url
                                }
                            })
                    else:
                        # Default behavior for messages without URLs
                        content = message['content']
                    threads.append({'role': message['role'], 'content': content})
            
            return {
                'success': True, 
                'messages': threads
            }
        except Exception as e:
            traceback.print_exc()
            print("create conversation error=>", e)
            raise ValueError(e.args[0])
    
    @staticmethod
    def createOpenAiResponseConversation(conversation, memory):
        try:
            threads = []
            if memory is not None:
                threads.append({'role': 'user', 'content': 'provide the summary of the previous conversation stored in the memory?'})
                threads.append({'role': 'assistant', 'content': f'Summary of previous conversations :  {memory}' })
            for message in conversation or []:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    if message['role'] == "assistant":
                        content = [{"type": "output_text", "text": message['content']}]
                    else:
                        content = [{"type": "input_text", "text": message['content']}]
                    
                    if 'urls' in message and isinstance(message['urls'], list):
                        for url in message['urls']:
                            content.append({
                                "type": "input_image",
                                "image_url": url
                            })
                    else:
                        # Default behavior for messages without URLs
                        content = message['content']
                    threads.append({'role': message['role'], 'content': content})
            
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
    async def createAnthropicConversation(conversation, memory):
        try:
            if conversation == None:
                conversation = []
            threads = []
            expected_role = 'user'
            
            if memory is not None:
                threads.append({'role': 'user', 'content': [{"type": "text", "text": f"GPT-Memory Data:- {memory}"}]})
                threads.append({'role': 'assistant', 'content': [{"type": "text", "text": "memory updated."}]})
            
            image_urls = [url for message in conversation for url in message.get('image_urls', [])]
            images_data = await fetch_images_b64(image_urls)
            images = {url : data for url, data in zip(image_urls, images_data)}
            
            for i, message in enumerate(conversation):
                if message['role'] not in ['assistant', 'user']:
                    raise ValueError(f"Invalid role '{message['role']}' at index {i}. Allowed roles are 'assistant' and 'user'.")
                if message['role'] != expected_role:
                    raise ValueError(f"Conversation format is not correct at index {i}. Expected role: {expected_role}")
                
                image_data = [{'type': 'image', 'source': {'type': 'base64', 'media_type': image_media_type, 'data': image_data }} for image_url in message.get('image_urls', []) for image_data, image_media_type in [images[image_url]]]
                threads.append({
                    'role': message['role'], 
                    'content': image_data + [{"type": "text", "text": message['content']}]
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

    def createGroqConversation(conversation, memory):
        try:
            threads = []
            
            # If memory is provided, add it as the first message
            if memory is not None:
                threads.append({'role': 'user', 'content': memory})
            
            # Loop through the conversation to build the message threads
            for message in conversation or []:
                if message['role'] not in ["tools_call", "tool"]:  # Skip tool-related roles
                    # Ensure content is a string (no image URLs, handle properly)
                    content = message['content']
                    
                    # If the role is 'assistant', ensure the content is a plain string
                    if message['role'] == 'assistant':
                        threads.append({'role': message['role'], 'content': content})
                    else:
                        # For other roles, wrap the content as 'text'
                        threads.append({'role': message['role'], 'content': [{"type": "text", "text": content}]})
            
            # Return the constructed messages in the required format for Groq
            return {
                'success': True,
                'messages': threads
            }
        
        except Exception as e:
            traceback.print_exc()
            print("create conversation error=>", e)
            raise ValueError(f"Error while creating conversation: {e}")



# Example usage:
# result = ConversationService.create_openai_conversation(conversation)
# result = ConversationService.create_gemini_conversation(conversation)
