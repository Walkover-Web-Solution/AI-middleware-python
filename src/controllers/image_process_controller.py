import json
import uuid
from google.cloud import storage
from google.oauth2 import service_account
from config import Config
from fastapi import HTTPException
from src.services.cache_service import find_in_cache, store_in_cache, client, REDIS_PREFIX

async def image_processing(request):
    body = await request.form()
    file = body.get('image')
    
    file_content = await file.read()
    
    try:
        # Set up Google Cloud Storage client
        credentials_dict = json.loads(Config.GCP_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)
        
        # Define the bucket and file path
        bucket = storage_client.bucket('resources.gtwy.ai')
        filename = f"uploads/{uuid.uuid4()}_{file.filename}"
        blob = bucket.blob(filename)
        
        # Upload the file to GCP
        blob.upload_from_string(file_content, content_type=file.content_type)
        image_url = f"https://resources.gtwy.ai/{filename}"
        
        return {
            'success': True,
            'image_url': image_url
        }
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in image processing: "+ str(e)})


async def file_processing(request):
    body = await request.form()
    file = body.get('file')
    if file is None:
        raise HTTPException(status_code=400, detail={"success": False, "error": "File not found"})
    
    # Extract thread parameters from form data
    thread_id = body.get('thread_id')
    sub_thread_id = body.get('sub_thread_id') 
    bridge_id = body.get('agent_id')
    
    file_content = await file.read()
    
    try:
        # Check if file is PDF
        is_pdf = file.content_type == 'application/pdf' or file.filename.lower().endswith('.pdf')
        
        # Set up Google Cloud Storage client
        credentials_dict = json.loads(Config.GCP_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        storage_client = storage.Client(credentials=credentials)
        
        # Define the bucket and file path
        bucket = storage_client.bucket('resources.gtwy.ai')
        filename = f"uploads/{uuid.uuid4()}_{file.filename}"
        blob = bucket.blob(filename)
        
        # Upload the file to GCP
        blob.upload_from_string(file_content, content_type=file.content_type)
        file_url = f"https://resources.gtwy.ai/{filename}"

        # If PDF and thread parameters exist, save to Redis cache
        if is_pdf and thread_id and bridge_id:
            cache_key = f"{bridge_id}_{thread_id}_{sub_thread_id or thread_id}"
            await store_in_cache(cache_key, [file_url], 604800)
        
        return {
            'success': True,
            'file_url': file_url
        }
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in image processing: "+ str(e)})