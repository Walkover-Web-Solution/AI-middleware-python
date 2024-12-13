import traceback
from openai import AsyncOpenAI 
import requests
from google.cloud import storage
from io import BytesIO
import uuid
import json
from config import Config
from google.oauth2 import service_account
from src.services.utils.apiservice import fetch

async def OpenAIImageModel(configuration, apiKey, execution_time_logs, timer):
    try:
        openai_config = AsyncOpenAI(api_key=apiKey)
        timer.start()
        chat_completion = await openai_config.images.generate(**configuration)
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Openai image stop")
        response = chat_completion.to_dict()
        timer.start()
        image_url = response['data'][0]['url']
        image_content, headers = await fetch(url=image_url, method='GET', image=True)

        credentials_dict = json.loads(Config.GCP_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)

        bucket = storage_client.bucket('ai_middleware_testing')
        
        filename = f"generated-images/{uuid.uuid4()}.png"
        blob = bucket.blob(filename)
        
        # Upload the image
        blob.upload_from_file(image_content, content_type='image/png')
        
        # Get the public URL
        gcp_url = f"https://storage.googleapis.com/ai_middleware_testing/{filename}"
        response['data'][0]['url'] = gcp_url
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Openai image stop")
        return {
            'success': True,
            'response': response
        }
    except Exception as error:
        execution_time_logs[len(execution_time_logs) + 1] = timer.stop("Openai image stop")
        print("runmodel error=>", error)
        traceback.print_exc()
        return {
            'success': False,
            'error': str(error)
        }