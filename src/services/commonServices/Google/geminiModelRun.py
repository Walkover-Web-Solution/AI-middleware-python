import traceback
import google.generativeai as genai
import json

async def gemini_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer):
    try:
        genai.configure(api_key=apikey)
        user_prompt = configuration.get('user', '')
        generation_config_params = {k: v for k, v in configuration.items() if k not in ['system_instruction', 'user', 'messages', 'model_name']}
        generation_config = genai.types.GenerationConfig(**generation_config_params)
        model = genai.GenerativeModel(model_name=configuration.get('model_name'), system_instruction=configuration.get('system_instruction', ''), generation_config=generation_config)
        timer.start()
        model_response = model.generate_content(user_prompt)
        response = model_response.to_dict()
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