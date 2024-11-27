import json
from groq import Groq
import traceback
from .baseService.utils import sendResponse
from ..commonServices.createConversations import ConversationService
from ..utils.ai_middleware_format import Response_formatter

async def chatbot_suggestions(conversations, response_format, assistant, user_msg):
    try:
        conversation = ConversationService.createOpenAiConversation(conversations).get('messages', [])
        configuration = {}
        configuration['max_tokens'] = 4000
        configuration['model'] = 'llama3-8b-8192'
        configuration['temperature'] = 0
        configuration['response_format'] = {"type" : "json_object"}
        user = "Generate suggestions " 
        system_prompt = "generate suggestions based on the user and assistant conversation. if you don't have context then return empty array. return suggestions in array.} JSON"
        configuration['messages'] = [ {"role": "system", "content": system_prompt }] + conversation + [{"role": "user", "content": user_msg }] +  [{"role": "assistant", "content": assistant['data']['content'] }] + ([{"role": "user", "content": user}] if user else [])
        apiKey = "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"
        Groq_config = Groq(api_key = apiKey)
        chat_completion = Groq_config.chat.completions.create(**configuration)
        response = chat_completion.to_dict()
        # suggestion = json.loads(response['choices'][0]['message']['content']).get('suggestions')
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