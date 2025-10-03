import traceback
from ..utils.apiservice import fetch_images_b64
from globals import *

class ConversationService:
    @staticmethod
    def createOpenAiConversation(conversation, memory, files):
        try:
            threads = []
            # Track distinct PDF URLs across the entire conversation
            seen_pdf_urls = set()
            
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
                            if not url.lower().endswith('.pdf'):
                                content.append({
                                    "type": "input_image",
                                    "image_url": url
                                })
                            elif url not in files and url not in seen_pdf_urls:
                                content.append({
                                    "type": "input_file",
                                    "file_url": url
                                })
                                # Add to seen URLs to prevent duplicates
                                seen_pdf_urls.add(url)
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
    async def createAnthropicConversation(conversation, memory, files):
        try:
            if conversation == None:
                conversation = []
            threads = []
            # Track distinct PDF URLs across the entire conversation
            seen_pdf_urls = set()
            
            if memory is not None:
                threads.append({'role': 'user', 'content': [{"type": "text", "text": f"GPT-Memory Data:- {memory}"}]})
                threads.append({'role': 'assistant', 'content': [{"type": "text", "text": "memory updated."}]})
            
            # Process image URLs if present
            image_urls = [url for message in conversation for url in message.get('image_urls', [])]
            images_data = await fetch_images_b64(image_urls) if image_urls else []
            images = {url: data for url, data in zip(image_urls, images_data)}
            
            valid_conversation = []
            expected_role = 'user'
            
            for message in conversation:
                if message['role'] not in ['assistant', 'user']:
                    continue  # Skip invalid roles
                
                # Skip messages with empty content
                if not message.get('content') or message['content'].strip() == '':
                    continue
                
                # If role doesn't match expected, skip this message
                if message['role'] != expected_role:
                    continue
                
                valid_conversation.append(message)
                expected_role = 'user' if expected_role == 'assistant' else 'assistant'
            for message in valid_conversation:
                content_items = []
                
                # Handle image URLs
                if message.get('image_urls'):
                    image_data = [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': image_media_type, 'data': image_data}}
                        for image_url in message.get('image_urls', [])
                        for image_data, image_media_type in [images.get(image_url)]
                        if image_url in images
                    ]
                    content_items.extend(image_data)
                
                # Handle URLs array for PDFs and other files
                if message.get('urls') and isinstance(message['urls'], list):
                    for url in message['urls']:
                        if url.lower().endswith('.pdf'):
                            # Only add PDF if not in files array and not seen before
                            if (files is None or url not in files) and url not in seen_pdf_urls:
                                content_items.append({
                                    "type": "document",
                                    "source": {
                                        "type": "url",
                                        "url": url
                                    }
                                })
                                # Add to seen URLs to prevent duplicates
                                seen_pdf_urls.add(url)
                        else:
                            # For non-PDF files (images), add as image
                            content_items.append({
                                "type": "image",
                                "source": {
                                    "type": "url",
                                    "url": url
                                }
                            })
                
                # Add text content
                content_items.append({"type": "text", "text": message['content']})
                
                threads.append({
                    'role': message['role'],
                    'content': content_items
                })
            print(threads)
            return {
                'success': True,
                'messages': threads
            }
        except Exception as e:
            logger.error(f"create conversation error=>, {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'messages': []
            }

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
            logger.error(f"create conversation error=>, {str(e)}, {traceback.format_exc()}")
            raise ValueError(f"Error while creating conversation: {str(e)}")

    @staticmethod
    def createOpenRouterConversation(conversation, memory):
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
                            if not url.lower().endswith('.pdf'):
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
            logger.error(f"create conversation error=>, {str(e)}")
            raise ValueError(e.args[0])

    @staticmethod
    def create_mistral_ai_conversation(conversation, memory):
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
                            if not url.lower().endswith('.pdf'):
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
            logger.error(f"create conversation error=>, {str(e)}")
            raise ValueError(e.args[0])

    @staticmethod
    def createGeminiConversation(conversation, memory):
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
                            if not url.lower().endswith('.pdf'):
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
            logger.error(f"create conversation error=>, {str(e)}")
            raise ValueError(e.args[0])

    @staticmethod
    def createOpenaiCompletionConversation(conversation, memory):
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
                            if not url.lower().endswith('.pdf'):
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
            logger.error(f"create conversation error=>, {str(e)}")
            raise ValueError(e.args[0])
    
    @staticmethod
    def createAiMlConversation(conversation, memory, files):
        try:
            threads = []
            # Track distinct PDF URLs across the entire conversation
            seen_pdf_urls = set()
            
            if memory is not None:
                threads.append({'role': 'user', 'content': 'provide the summary of the previous conversation stored in the memory?'})
                threads.append({'role': 'assistant', 'content': f'Summary of previous conversations :  {memory}' })
            for message in conversation or []:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    content = [{"type": "text", "text": message['content']}]
                    
                    if 'urls' in message and isinstance(message['urls'], list):
                        for url in message['urls']:
                            if not url.lower().endswith('.pdf'):
                                content.append({
                                    "type": "input_image",
                                    "image_url": url
                                })
                            elif url not in files and url not in seen_pdf_urls:
                                content.append({
                                    "type": "input_file",
                                    "file_url": url
                                })
                                # Add to seen URLs to prevent duplicates
                                seen_pdf_urls.add(url)
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