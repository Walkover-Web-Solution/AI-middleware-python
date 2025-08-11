import traceback
from openai import AsyncOpenAI 
import uuid
import asyncio
from src.services.utils.gcp_upload_service import uploadDoc



async def OpenAIImageModel(configuration, apiKey, execution_time_logs, timer):
    try:
        openai_config = AsyncOpenAI(api_key=apiKey)
        timer.start()
        chat_completion = await openai_config.images.generate(**configuration)
        execution_time_logs.append({"step": "OpenAI image Processing time", "time_taken": timer.stop("OpenAI image Processing time")})
        response = chat_completion.to_dict()
        
        # Process all images in the response data array
        for i, image_data in enumerate(response['data']):
            # Get original OpenAI image URL
            original_image_url = image_data['url']
            
            # Generate predictable GCP URL immediately and start background upload
            gcp_url = await uploadDoc(
                file=original_image_url,
                folder='generated-images',
                real_time=False,
                content_type='image/png'
            )
            
            # Add both URLs to response
            response['data'][i]['original_url'] = original_image_url
            response['data'][i]['url'] = gcp_url  # Primary URL (GCP)
        
        return {
            'success': True,
            'response': response
        }
    except Exception as error:
        execution_time_logs.append({"step": "OpenAI image Processing time", "time_taken": timer.stop("OpenAI image Processing time")})
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }