import traceback
from openai import AsyncOpenAI 
from google.cloud import storage
import uuid
import json
import asyncio
from config import Config
from google.oauth2 import service_account
from src.services.utils.apiservice import fetch

async def upload_to_gcp_background(image_url: str, filename: str):
    """
    Background task to upload image from OpenAI URL to GCP storage
    """
    try:
        
        # Fetch image content
        image_content, headers = await fetch(url=image_url, method='GET', image=True)
        
        # Setup GCP credentials and client
        credentials_dict = json.loads(Config.GCP_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)
        
        bucket = storage_client.bucket('resources.gtwy.ai')
        blob = bucket.blob(filename)
        
        # Upload the image
        blob.upload_from_file(image_content, content_type='image/png')
        
    except Exception as error:
        print(f"Background upload failed for {filename}: {str(error)}")
        traceback.print_exc()

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
            
            # Generate predictable GCP URL immediately
            filename = f"generated-images/{uuid.uuid4()}.png"
            gcp_url = f"https://resources.gtwy.ai/{filename}"
            
            # Add both URLs to response
            response['data'][i]['original_url'] = original_image_url
            response['data'][i]['url'] = gcp_url  # Primary URL (GCP)
            
            # Start background upload task (fire and forget)
            asyncio.create_task(upload_to_gcp_background(original_image_url, filename))
        
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