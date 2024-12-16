import traceback
import google.generativeai as genai
import json

async def gemini_runmodel(configuration, apikey, execution_time_logs, bridge_id, timer):
    try:
        genai.configure(api_key=apikey)
        user_prompt = configuration.get('user', '')
        # Create generation config
        generation_config = genai.types.GenerationConfig(
            temperature= configuration.get('temperature', 0.1),
            max_output_tokens=configuration.get('max_output_tokens', 252),
            candidate_count=configuration.get('candidate_count', None),
            stop_sequences=configuration.get('stop_sequences', None),
            top_p=configuration.get('top_p', None),
            top_k=configuration.get('top_k', None),
            # response_mime_type=configuration.get('response_mime_type', None),
            response_schema=configuration.get('response_schema', None),
        )
        model = genai.GenerativeModel(
            model_name=configuration.get('model', 'gemini-1.5-pro'),
            system_instruction=configuration.get('system', ''),
            generation_config=generation_config
        )

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