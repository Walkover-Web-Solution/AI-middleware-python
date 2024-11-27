import json
from groq import Groq
import traceback
from .baseService.utils import sendResponse
from ..commonServices.createConversations import ConversationService
from ..utils.ai_middleware_format import Response_formatter
from config import Config

async def chatbot_suggestions(conversations, response_format, assistant, user_msg):
    try:
        conversation = ConversationService.createOpenAiConversation(conversations).get('messages', [])
        configuration = {}
        configuration['max_tokens'] = 1000
        configuration['model'] = 'llama-3.1-70b-versatile'
        configuration['temperature'] = 0
        configuration['response_format'] = {"type" : "json_object"}
        user = "Generate suggestions " 
        system_prompt = "Based on the previous conversation between the user and assistant, generate an array containing only 3 suggestions that are directly related to the topics discussed. Each suggestion should be no more than 5 words. If there is no context from the conversation history, then return an empty array. Return the suggestions as a JSON array of strings without any additional text or structure. JSON Response Instructions: {\"suggestions\": [\"suggestion1\", \"suggestion2\", ...]}"
        configuration['messages'] = [ {"role": "system", "content": system_prompt }] + [{"role": "user", "content": user_msg }] +  [{"role": "assistant", "content": assistant['data']['content'] }] + ([{"role": "user", "content": user}] if user else [])
        apiKey = Config.OPTIONS_APIKEY
        Groq_config = Groq(api_key = apiKey)
        chat_completion = Groq_config.chat.completions.create(**configuration)
        response = chat_completion.to_dict()
        result = await Response_formatter(response, "groq", {})
        result['data']['suggestions']= json.loads(result.get('data').get('content')).get('suggestions')
        await sendResponse(response_format, result, success=True)
        return
    except Exception as error:
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }