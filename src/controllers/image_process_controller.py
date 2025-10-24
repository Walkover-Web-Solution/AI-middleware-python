import json
import uuid
from fastapi import HTTPException
from src.services.cache_service import find_in_cache, store_in_cache, client, REDIS_PREFIX
from src.services.utils.gcp_upload_service import uploadDoc
from google import genai
import tempfile
import os
from config import Config
from src.configs.constant import redis_keys

async def image_processing(request):
    body = await request.form()
    file = body.get('image')
    
    file_content = await file.read()
    
    try:
        # Upload file using common GCP upload function
        image_url = await uploadDoc(
            file=file_content,
            folder='uploads',
            real_time=True,
            content_type=file.content_type,
            original_filename=file.filename
        )
        
        return {
            'success': True,
            'image_url': image_url
        }
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in image processing: "+ str(e)})


async def file_processing(request):
    body = await request.form()
    
    # Check for both 'file' and 'video' in form data
    file = body.get('file') or body.get('video')
    
    if file is None:
        raise HTTPException(status_code=400, detail={"success": False, "error": "File not found"})
    
    # Extract thread parameters from form data
    thread_id = body.get('thread_id')
    sub_thread_id = body.get('sub_thread_id') 
    bridge_id = body.get('agent_id')
    
    file_content = await file.read()
    
    # Check file type
    is_pdf = file.content_type == 'application/pdf' or file.filename.lower().endswith('.pdf')
    is_video = file.content_type == 'video/mp4' or file.filename.lower().endswith('.mp4')
    
    try:
        
        # Handle video files with Gemini processing
        if is_video:
            # Get API key from form data or use default
            api_key = Config.GEMINI_APIKEY
            
            # Create Gemini client
            gemini_client = genai.Client(api_key=api_key)
            
            # Create temporary file to upload to Gemini
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Upload file to Gemini
                gemini_file = gemini_client.files.upload(file=temp_file_path)
                
                # Convert file object to dictionary for JSON serialization
                file_data = {
                    'name': gemini_file.name,
                    'display_name': gemini_file.display_name,
                    'mime_type': gemini_file.mime_type,
                    'size_bytes': gemini_file.size_bytes,
                    'create_time': gemini_file.create_time.isoformat() if gemini_file.create_time else None,
                    'expiration_time': gemini_file.expiration_time.isoformat() if gemini_file.expiration_time else None,
                    'update_time': gemini_file.update_time.isoformat() if gemini_file.update_time else None,
                    'sha256_hash': gemini_file.sha256_hash,
                    'uri': gemini_file.uri,
                    'download_uri': gemini_file.download_uri,
                    'state': str(gemini_file.state),
                    'source': str(gemini_file.source),
                    'video_metadata': gemini_file.video_metadata,
                    'error': gemini_file.error
                }
                
                return {
                    'success': True,
                    'file_data': file_data,
                    'message': 'Video uploaded to Gemini successfully'
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Handle regular files (non-video) with GCP upload
        else:
            # Upload file using common GCP upload function
            file_url = await uploadDoc(
                file=file_content,
                folder='uploads',
                real_time=True,
                content_type=file.content_type,
                original_filename=file.filename
            )

            # If PDF and thread parameters exist, save to Redis cache
            if is_pdf and thread_id and bridge_id:
                cache_key = f"{redis_keys['pdf_url_']}{bridge_id}_{thread_id}_{sub_thread_id or thread_id}"
                await store_in_cache(cache_key, [file_url], 604800)
            
            return {
                'success': True,
                'file_url': file_url
            }
            
    except Exception as e:
        # Handle exceptions and return an error response
        error_message = "Error in video processing: " if is_video else "Error in file processing: "
        raise HTTPException(status_code=400, detail={"success": False, "error": error_message + str(e)})