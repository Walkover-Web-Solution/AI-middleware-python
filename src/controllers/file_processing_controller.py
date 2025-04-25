import json
import uuid
from google.cloud import storage
from google.oauth2 import service_account
from config import Config

async def file_processing(request):
    body = await request.form()
    file = body.get('file')
    
    # Check if file is PDF
    if not file.filename.lower().endswith('.pdf'):
        return {
            'success': False,
            'error': 'Only PDF files are allowed'
        }
    
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
        blob.upload_from_string(file_content, content_type='application/pdf')
        file_url = f"https://resources.gtwy.ai/{filename}"
        
        return {
            'success': True,
            'file_url': file_url
        }
    except Exception as e:
        # Handle exceptions and return an error response
        return {
            'success': False,
            'error': str(e)
        }