import traceback
import google.generativeai as genai
import json

async def gemini_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer):
    try:
        genai.configure(api_key=apikey)
        model = genai.GenerativeModel(configuration['model'])
        timer.start()
        
        chat = model.start_chat(
            # Need to add conversation arary in history
            history=[
                {"role": "user", "parts": ""},
                {"role": "model", "parts": ""}
            ]  
        )
        model_response = chat.send_message(configuration['user']) #need to ajust with system_prompt and messages
        response = [chunk.text for chunk in model_response]
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Gemini chat completion")
        print(11, json.dumps(configuration), 22, bridge_id)
        return {
            'success': True,
            'response': response
        }
    
    except Exception as error:
        print("Gemini runmodel error=>", error)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Gemini chat completion")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }