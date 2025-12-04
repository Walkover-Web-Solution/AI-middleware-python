import traceback
import aiohttp
import base64
from ..utils.apiservice import fetch_images_b64
from globals import *

class ConversationService:
    @staticmethod
    async def _convert_url_to_base64(url):
        """
        Convert HTTP URL to base64 data URL for Gemini compatibility
        """
        try:
            import ssl
            # Create SSL context that doesn't verify certificates for internal resources
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('content-type', 'application/octet-stream')
                        
                        # Encode to base64
                        base64_content = base64.b64encode(content).decode('utf-8')
                        
                        # Return as data URL
                        return f"data:{content_type};base64,{base64_content}"
                    else:
                        logger.warning(f"Failed to fetch URL {url}: HTTP {response.status}")
                        return url
        except Exception as e:
            logger.error(f"Error converting URL to base64: {e}")
            return url
    
    @staticmethod
    def _is_http_url(url):
        """
        Check if the URL is an HTTP/HTTPS URL
        """
        return isinstance(url, str) and (url.startswith('http://') or url.startswith('https://'))
    
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
                    
                    if 'user_urls' in message and isinstance(message['user_urls'], list):
                        for url in message['user_urls']:
                            if url.get('type') == 'image':
                                content.append({
                                    "type": "input_image",
                                    "image_url": url.get('url')
                                })
                            elif url.get('url') not in files and url.get('url') not in seen_pdf_urls:
                                content.append({
                                    "type": "input_file",
                                    "file_url": url.get('url')
                                })
                                # Add to seen URLs to prevent duplicates
                                seen_pdf_urls.add(url.get('url'))
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
            image_urls = [url.get('url') for message in conversation for url in message.get('user_urls', [])]
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
                if message.get('user_urls'):
                    image_data = []
                    for url_info in message['user_urls']:
                        url = url_info.get("url")
                        if url in images:
                            img_type = url_info.get("type")
                            if img_type == 'image':
                                image_data.append({
                                    'type': 'image',
                                    'source': {
                                        'type': 'base64',
                                        'media_type': images[url][1],
                                        'data': images[url][0]
                                    }
                                })
                            elif img_type == 'pdf':
                                image_data.append({
                                    'type': 'document',
                                    'source': {
                                        'type': 'url',
                                        'url': url
                                    }
                                })
                            else:
                                image_data.append({
                                    'type': 'image',
                                    'source': {
                                        'type': 'url',
                                        'url': url
                                    }
                                })


                    content_items.extend(image_data)
                
                # Add text content
                content_items.append({"type": "text", "text": message['content']})
                
                threads.append({
                    'role': message['role'],
                    'content': content_items
                })
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
    def createGrokConversation(conversation, memory, files=None, image_urls=None):
        try:
            threads = []

            if memory is not None:
                threads.append({'role': 'user', 'content': 'provide the summary of the previous conversation stored in the memory?'})
                threads.append({'role': 'assistant', 'content': f'Summary of previous conversations :  {memory}'})

            for message in conversation or []:
                if message['role'] in ["tools_call", "tool"]:
                    continue

                content = [{"type": "text", "text": message['content']}]

                if 'urls' in message and isinstance(message['urls'], list):
                    for url in message['urls']:
                        if not url.lower().endswith('.pdf'):
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": url}
                            })

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
    async def createGeminiConversation(conversation, memory, files):
        try:
            threads = []
            # Track distinct file URLs across the entire conversation
            seen_file_urls = set()
            
            if memory is not None:
                threads.append({'role': 'user', 'content': 'provide the summary of the previous conversation stored in the memory?'})
                threads.append({'role': 'assistant', 'content': f'Summary of previous conversations :  {memory}' })
            for message in conversation or []:
                if message['role'] != "tools_call" and message['role'] != "tool":
                    if message['role'] == "assistant":
                        content = [{"type": "text", "text": message['content']}]
                    else:
                        content = [{"type": "text", "text": message['content']}]
                    
                    # Handle user_urls similar to OpenAI format
                    if 'user_urls' in message and isinstance(message['user_urls'], list):
                        for url in message['user_urls']:
                            if url.get('type') == 'image':
                                # Pass HTTP URLs directly to Gemini (will fallback if not supported)
                                content.append({
                                    "type": "image_url",
                                    "image_url": {"url": url.get('url')}
                                })
                            elif url.get('url') not in files and url.get('url') not in seen_file_urls:
                                # Handle non-image files as text content for Gemini
                                content.append({
                                    "type": "text",
                                    "text": f"File: {url.get('url')}"
                                })
                                # Add to seen URLs to prevent duplicates
                                seen_file_urls.add(url.get('url'))
                    
                    # Handle legacy 'urls' format for backward compatibility
                    elif 'urls' in message and isinstance(message['urls'], list):
                        for url in message['urls']:
                            if not url.lower().endswith('.pdf'):
                                # Pass HTTP URLs directly to Gemini (will fallback if not supported)
                                content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url": url
                                    }
                                })
                            elif url not in seen_file_urls:
                                content.append({
                                    "type": "text",
                                    "text": f"File: {url}"
                                })
                                seen_file_urls.add(url)
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
                    has_media = False
                    content = [{"type": "text", "text": message['content']}]
                    
                    if 'user_urls' in message and isinstance(message['user_urls'], list):
                        for url in message['user_urls']:
                            if url.get('type') == 'image':
                                content.append({
                                    "type": "image_url",
                                    "image_url": {
                                        "url":url.get('url')
                                    }
                                })
                                has_media = True
                            elif url.get('url') not in files and url.get('url') not in seen_pdf_urls:
                                content.append({
                                    "type": "input_file",
                                    "file_url": {
                                        "url":url.get('url')
                                    }
                                })
                                has_media = True
                                # Add to seen URLs to prevent duplicates
                                seen_pdf_urls.add(url.get('url'))
                    
                    # Use string format for AI/ML when no media, array format when media present
                    if not has_media:
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