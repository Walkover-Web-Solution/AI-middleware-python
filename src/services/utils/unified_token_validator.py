# import tiktoken
# import json
# import anthropic
# from google import genai
# from google.genai import types
# from src.configs.model_configuration import model_config_document
# from src.services.utils.logger import logger


# def validate_openai_token_limit(configuration: dict, model_name: str, service: str, safety_margin: float = 0.1) -> None:
#     """
#     Validate token count for OpenAI models using tiktoken with database-driven encoding selection.
#     Raises exception if token limit is exceeded, otherwise returns None.
    
#     Args:
#         configuration: The request configuration
#         model_name: Name of the OpenAI model
#         service: Service name (e.g., 'openai', 'openai_response')
#         safety_margin: Percentage to reserve for response (default 10%)
    
#     Raises:
#         ValueError: If token count exceeds the model's context window limit
#     """
#     try:
#         # Get model type and determine encoding
#         model_type = model_config_document.get(service, {}).get(model_name, {}).get('validationConfig', {}).get('type')
        
#         if model_type == 'reasoning':
#             encoding_name = 'o200k_base'
#         else:  # 'chat' or any other type
#             encoding_name = 'cl100k_base'
            
#         encoding = tiktoken.get_encoding(encoding_name)
        
#         # Convert configuration to JSON and count tokens
#         config_text = json.dumps(configuration, ensure_ascii=False, separators=(',', ':'))
#         token_count = len(encoding.encode(config_text))
        
#         # Get context window from model configuration
#         context_window = model_config_document.get(service, {}).get(model_name, {}).get('validationConfig', {}).get('context_window')
        
#         if context_window is None:
#             # No context window configured - skip validation and allow request
#             logger.info(f"No context window configured for {service}/{model_name} - skipping token validation")
#             return
        
#         context_window = int(context_window)
        
#         # Calculate max allowed tokens (with safety margin for response)
#         max_allowed = int(context_window * (1 - safety_margin))
        
#         # Check if within limits
#         if token_count <= max_allowed:
#             logger.info(f"OpenAI token validation passed for {model_name}: {token_count}/{max_allowed} tokens")
#             return
#         else:
#             # Token limit exceeded - raise exception
#             error_message = f"Token validation failed: {token_count} tokens exceeds limit of {max_allowed} (context window: {context_window}, safety margin: {safety_margin*100}%)"
#             logger.error(f"OpenAI token validation failed for {model_name}: {error_message}")
#             raise ValueError(error_message)
        
#     except ValueError:
#         # Re-raise ValueError (token limit exceeded)
#         raise
#     except Exception as e:
#         logger.error(f"Error validating OpenAI tokens for {model_name}: {str(e)}")
#         # On error, allow the request to proceed (graceful degradation)
#         return


# def validate_anthropic_token_limit(configuration: dict, model_name: str, service: str, api_key: str, safety_margin: float = 0.1) -> None:
#     """
#     Validate token count for Anthropic models using their native count_tokens method.
#     Raises exception if token limit is exceeded, otherwise returns None.
    
#     Args:
#         configuration: The request configuration (messages, system, etc.)
#         model_name: Name of the Anthropic model
#         service: Service name (e.g., 'anthropic')
#         api_key: Anthropic API key
#         safety_margin: Percentage to reserve for response (default 10%)
    
#     Raises:
#         ValueError: If token count exceeds the model's context window limit
#     """
#     try:
#         # Initialize Anthropic client
#         client = anthropic.Anthropic(api_key=api_key)
        
#         # Prepare parameters for count_tokens API - only include supported parameters
#         count_params = {
#             'model': configuration.get('model', model_name),
#             'messages': configuration.get('messages', [])
#         }
        
#         # Add optional parameters if they exist in configuration
#         if 'system' in configuration:
#             count_params['system'] = configuration['system']
#         if 'tools' in configuration:
#             count_params['tools'] = configuration['tools']
#         if 'tool_choice' in configuration:
#             count_params['tool_choice'] = configuration['tool_choice']
        
#         # Count tokens using Anthropic's native method with specific parameters
#         response = client.messages.count_tokens(**count_params)
        
#         token_count = response.input_tokens
        
#         # Get context window from model configuration
#         context_window = model_config_document.get(service, {}).get(model_name, {}).get('validationConfig', {}).get('context_window')
        
#         if context_window is None:
#             # No context window configured - skip validation and allow request
#             logger.info(f"No context window configured for {service}/{model_name} - skipping token validation")
#             return
        
#         context_window = int(context_window)
        
#         # Calculate max allowed tokens (with safety margin for response)
#         max_allowed = int(context_window * (1 - safety_margin))
        
#         # Check if within limits
#         if token_count <= max_allowed:
#             logger.info(f"Anthropic token validation passed for {model_name}: {token_count}/{max_allowed} tokens")
#             return
#         else:
#             # Token limit exceeded - raise exception
#             error_message = f"Token validation failed: {token_count} tokens exceeds limit of {max_allowed} (context window: {context_window}, safety margin: {safety_margin*100}%)"
#             logger.error(f"Anthropic token validation failed for {model_name}: {error_message}")
#             raise ValueError(error_message)
        
#     except ValueError:
#         # Re-raise ValueError (token limit exceeded)
#         raise
#     except Exception as e:
#         logger.error(f"Error validating Anthropic tokens for {model_name}: {str(e)}")
#         # On error, allow the request to proceed (graceful degradation)
#         return


# def validate_gemini_token_limit(configuration: dict, model_name: str, service: str, api_key: str, safety_margin: float = 0.1) -> None:
#     """
#     Validate token count for Gemini models using Google's native genai library.
#     Raises exception if token limit is exceeded, otherwise returns None.
    
#     Args:
#         configuration: The request configuration (messages, etc.)
#         model_name: Name of the Gemini model
#         service: Service name (e.g., 'gemini')
#         api_key: Google API key
#         safety_margin: Percentage to reserve for response (default 10%)
    
#     Raises:
#         ValueError: If token count exceeds the model's context window limit
#     """
#     try:
#         # Initialize Google GenAI client
#         client = genai.Client(api_key=api_key)
        
#         # Convert OpenAI-style messages to Gemini content format
#         contents = []
#         messages = configuration.get('messages', [])
        
#         for message in messages:
#             role = message.get('role', 'user')
#             content_text = message.get('content', '')
            
#             # Map OpenAI roles to Gemini roles
#             if role == 'assistant':
#                 gemini_role = 'model'
#             else:
#                 gemini_role = 'user'
            
#             # Create Gemini content
#             content = types.Content(
#                 role=gemini_role,
#                 parts=[types.Part(text=content_text)]
#             )
#             contents.append(content)
        
#         # Count tokens using Gemini's native method
#         model = configuration.get('model', model_name)
#         token_response = client.models.count_tokens(
#             model=model,
#             contents=contents
#         )
        
#         token_count = token_response.total_tokens
        
#         # Get context window from model configuration
#         context_window = model_config_document.get(service, {}).get(model_name, {}).get('validationConfig', {}).get('context_window')
        
#         if context_window is None:
#             # No context window configured - skip validation and allow request
#             logger.info(f"No context window configured for {service}/{model_name} - skipping token validation")
#             return
        
#         context_window = int(context_window)
        
#         # Calculate max allowed tokens (with safety margin for response)
#         max_allowed = int(context_window * (1 - safety_margin))
        
#         # Check if within limits
#         if token_count <= max_allowed:
#             logger.info(f"Gemini token validation passed for {model_name}: {token_count}/{max_allowed} tokens")
#             return
#         else:
#             # Token limit exceeded - raise exception
#             error_message = f"Token validation failed: {token_count} tokens exceeds limit of {max_allowed} (context window: {context_window}, safety margin: {safety_margin*100}%)"
#             logger.error(f"Gemini token validation failed for {model_name}: {error_message}")
#             raise ValueError(error_message)
        
#     except ValueError:
#         # Re-raise ValueError (token limit exceeded)
#         raise
#     except Exception as e:
#         logger.error(f"Error validating Gemini tokens for {model_name}: {str(e)}")
#         # On error, allow the request to proceed (graceful degradation)
#         return


# def validate_mistral_token_limit(configuration: dict, model_name: str, service: str, safety_margin: float = 0.1) -> None:
#     """
#     Validate token count for Mistral models using their native mistral-common tokenizer.
#     Raises exception if token limit is exceeded, otherwise returns None.
    
#     Args:
#         configuration: The request configuration (messages, tools, etc.)
#         model_name: Name of the Mistral model
#         service: Service name (e.g., 'mistral')
#         safety_margin: Percentage to reserve for response (default 10%)
    
#     Raises:
#         ValueError: If token count exceeds the model's context window limit
#     """
#     try:
#         from mistral_common.protocol.instruct.messages import UserMessage, AssistantMessage, SystemMessage
#         from mistral_common.tokens.tokenizers.mistral import MistralTokenizer
#         from mistral_common.protocol.instruct.request import ChatCompletionRequest
        
#         # Initialize Mistral tokenizer for the specific model
#         tokenizer = MistralTokenizer.from_model(model_name)
        
#         # Convert OpenAI-style messages to Mistral message format
#         mistral_messages = []
#         for message in configuration.get('messages', []):
#             role = message.get('role', 'user')
#             content = message.get('content', '')
            
#             if role == 'system':
#                 mistral_messages.append(SystemMessage(content=content))
#             elif role == 'assistant':
#                 mistral_messages.append(AssistantMessage(content=content))
#             else:
#                 mistral_messages.append(UserMessage(content=content))
        
#         # Create ChatCompletionRequest with full configuration
#         chat_request = ChatCompletionRequest(
#             model=configuration.get('model', model_name),
#             messages=mistral_messages,
#             tools=configuration.get('tools'),
#         )
        
#         # Count tokens using Mistral's native tokenizer
#         tokenized = tokenizer.encode_chat_completion(chat_request)
#         token_count = len(tokenized.tokens)
        
#         # Get context window from model configuration
#         context_window = model_config_document.get(service, {}).get(model_name, {}).get('validationConfig', {}).get('context_window')
        
#         if context_window is None:
#             # No context window configured - skip validation and allow request
#             logger.info(f"No context window configured for {service}/{model_name} - skipping token validation")
#             return
        
#         context_window = int(context_window)
        
#         # Calculate max allowed tokens (with safety margin for response)
#         max_allowed = int(context_window * (1 - safety_margin))
        
#         # Check if within limits
#         if token_count <= max_allowed:
#             logger.info(f"Mistral token validation passed for {model_name}: {token_count}/{max_allowed} tokens")
#             return
#         else:
#             # Token limit exceeded - raise exception
#             error_message = f"Token validation failed: {token_count} tokens exceeds limit of {max_allowed} (context window: {context_window}, safety margin: {safety_margin*100}%)"
#             logger.error(f"Mistral token validation failed for {model_name}: {error_message}")
#             raise ValueError(error_message)
        
#     except ValueError:
#         # Re-raise ValueError (token limit exceeded)
#         raise
#     except Exception as e:
#         logger.error(f"Error validating Mistral tokens for {model_name}: {str(e)}")
#         # On error, allow the request to proceed (graceful degradation)
#         return
