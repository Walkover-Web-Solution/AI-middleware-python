import traceback
from google import genai
from google.genai import types
import uuid
import time
from io import BytesIO
from PIL import Image
import base64
from src.services.utils.gcp_upload_service import uploadDoc

async def gemini_image_model(configuration, apikey, execution_time_logs, timer):
    """Generate Gemini image output, upload it, and return structured data."""
    try:
        # Initialize the Gemini client
        client = genai.Client(api_key=apikey)
        contents = configuration.pop('prompt', '')
        model = configuration.pop('model')
        configuration['response_modalities'] = ['TEXT', 'IMAGE']
        
        
        # Generate content using Gemini 2.0 Flash model
        timer.start()
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(**configuration) if configuration else None
        )
        
        execution_time_logs.append({"step": "Gemini image Processing time", "time_taken": timer.stop("Gemini image Processing time")})
        
        text_content = []
        gcp_url = None
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                text_content.append(part.text)
            elif part.inline_data is not None:
                # Convert inline data to PIL Image
                image = Image.open(BytesIO(part.inline_data.data))
                
                # Convert PIL Image to bytes for upload
                img_buffer = BytesIO()
                image.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Upload to GCP using common upload function
                gcp_url = await uploadDoc(
                    file=img_buffer,
                    folder='generated-images',
                    real_time=True,
                    content_type='image/png'
                )
                
        # Format response to match expected structure
        response = {
            'data': [
                {
                    'url': gcp_url,
                    'text_content': text_content
                }
            ]
        }
        
        return {
            'success': True,
            'response': response
        }
        
    except Exception as error:
        execution_time_logs.append({"step": "Gemini image Processing time", "time_taken": timer.stop("Gemini image Processing time")})
        print("gemini_image_model error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }
