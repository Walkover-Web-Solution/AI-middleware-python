import json
import uuid
from fastapi import HTTPException
from src.services.cache_service import find_in_cache, store_in_cache, client, REDIS_PREFIX
from src.services.utils.gcp_upload_service import uploadDoc

async def image_processing(request):
    """Upload an image from form data and return its public URL."""
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
    """Upload a file, caching PDF urls against thread identifiers when provided."""
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
            cache_key = f"{bridge_id}_{thread_id}_{sub_thread_id or thread_id}"
            await store_in_cache(cache_key, [file_url], 604800)
        
        return {
            'success': True,
            'file_url': file_url
        }
    except Exception as e:
        # Handle exceptions and return an error response
        raise HTTPException(status_code=400, detail={"success": False, "error": "Error in image processing: "+ str(e)})
