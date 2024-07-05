import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import traceback

def run_chat(configuration, api_key, service):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(configuration.get("model"))

        safety_settings = [
            {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
            {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE}
        ]
        configuration["safetySettings"] = safety_settings

        if service == "chat":
            chat = model.start_chat(
                # generation_config=configuration.get("generationConfig"),
                history=configuration.get("history"),
                # safety_settings=configuration.get("safetySettings")
            )
            response = chat.send_message(configuration.get("user_input")).to_dict()
            # history = chat.get_history()
            # msg_content = {
            #     "role": "user",
            #     "parts": [{"text": configuration.get("user_input")}]
            # }
            contents =   response["candidates"][0]["content"]["parts"][0]["text"]

            input_tokens = model.count_tokens(contents).total_tokens
            output_tokens = model.count_tokens(response["candidates"][0]["content"]).total_tokens
            return {
                "success": True,
                "modelResponse": response,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                }
            }
        
        return {
            "success": False,
            "error": "operation undefined!"
        }

    except Exception as error:
        traceback.print_exc()
        print("gemini error=>", error)
        return {
            "success": False,
            "error": str(error)
        }

# Exporting the function
__all__ = ["run_chat"]
