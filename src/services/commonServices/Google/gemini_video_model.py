import traceback
from google import genai
from google.genai import types
import time

async def gemini_video_model(configuration, apikey, execution_time_logs, timer, file_data, prompt=None, youtube_url=None):
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=apikey)
        model = configuration.pop('model')
        youtube_url = configuration.pop('youtube_url', None)
        prompt = configuration.pop('prompt', None)
        print("harsh: configurations=>", configuration, "\n\n")
        timer.start()
        
        # Prepare contents based on YouTube URL or uploaded file
        print("harsh: Preparing contents for Gemini video model...")
        print(f"harsh: youtube_url: {youtube_url}")
        print(f"harsh: prompt: {prompt}")
        print(f"harsh: file_data: {file_data}")
        
        if youtube_url:
            print("harsh: Using YouTube URL path...")
            # Use YouTube URL with structured content
            print(f"harsh: Creating FileData with URI: {youtube_url}")
            file_part = types.Part(
                file_data=types.FileData(file_uri=youtube_url)
            )
            print(f"harsh: Created file_part: {file_part}")
            
            prompt_part = types.Part(text=prompt) if prompt else None
            print(f"harsh: Created prompt_part: {prompt_part}")
            
            contents = types.Content(
                parts=[file_part, prompt_part]
            )
            print(f"harsh: Created contents with parts: {contents}")
            
            # Remove None parts
            print("harsh: Removing None parts from contents...")
            contents.parts = [part for part in contents.parts if part is not None]
            print(f"harsh: Final contents after removing None: {contents}")
        else:
            print("harsh: Using uploaded file path...")
            # For uploaded files, use the simpler approach from test.py
            if prompt:
                print(f"harsh: Creating contents with file_data and prompt")
                contents = [file_data, prompt]
            else:
                print(f"harsh: Creating contents with file_data only")
                contents = [file_data]
            print(f"harsh: Final contents: {contents}")
        
        # Generate content
        print("harsh: contents=>", contents, "\n\n")
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config= None
        )
        execution_time_logs.append({"step": "Gemini video content generation", "time_taken": timer.stop("Gemini video content generation")})
        
        # Extract text content from response
        text_content = []
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_content.append(part.text)
        
        # Join text content into a single string for response.data.content
        content_text = ' '.join(text_content) if text_content else ''
        
        # Format response to match expected structure
        response_data = {
            'data': [
                {
                    'text_content': content_text,
                    'file_reference': file_data
                }
            ]
        }
        return {
            'success': True,
            'response': response_data
        }
        
    except Exception as error:
        execution_time_logs.append({"step": "Gemini video processing error", "time_taken": timer.stop("Gemini video processing error")})
        print("gemini_video_model error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
