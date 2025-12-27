import json
import uuid
import tempfile
import os
from google import genai
from google.genai import types

async def create_batch_file(batch_requests, apiKey):
    """
    Creates a JSONL file and uploads it to Gemini File API.
    
    Args:
        batch_requests: List of JSON strings (JSONL entries)
        apiKey: Gemini API key
        
    Returns:
        Uploaded file object from Gemini File API
    """
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=apiKey)
        
        # Create JSONL file content
        jsonl_content = "\n".join(batch_requests)
        
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(jsonl_content)
            temp_file_path = temp_file.name
        
        try:
            # Upload the JSONL file to Gemini File API
            uploaded_file = client.files.upload(
                file=temp_file_path,
                config=types.UploadFileConfig(
                    display_name=f'batch-{uuid.uuid4()}',
                    mime_type='application/jsonl'
                )
            )
            return uploaded_file
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        print("Error in Gemini create_batch_file:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise

async def process_batch_file(uploaded_file, apiKey, model):
    """
    Creates a batch job using the uploaded file.
    
    Args:
        uploaded_file: File object from create_batch_file
        apiKey: Gemini API key
        model: Model name to use for batch processing
        
    Returns:
        Batch job object
    """
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=apiKey)
        
        # Create batch job with the uploaded file
        batch_job = client.batches.create(
            model=model,
            src=uploaded_file.name,
            config={
                'display_name': f'batch-job-{uuid.uuid4()}',
            }
        )
        print(f"Created batch job: {batch_job.name}")
        return batch_job
    except Exception as e:
        print(f"Error in Gemini process_batch_file: {e}")
        raise

async def retrieve_batch_status(batch_id, apiKey):
    """
    Retrieves the status of a batch job.
    
    Args:
        batch_id: Batch job name
        apiKey: Gemini API key
        
    Returns:
        Batch job object with current status
    """
    try:
        # Initialize Gemini client
        client = genai.Client(api_key=apiKey)
        
        # Get batch job status
        batch = client.batches.get(name=batch_id)
        print(f"Batch status: {batch.state}")
        return batch
    except Exception as e:
        print(f"Error in Gemini retrieve_batch_status: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping):
    """
    Handle Gemini batch processing - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: Gemini API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        Tuple of (results, is_completed)
    """
    batch = await retrieve_batch_status(batch_id, apikey)
    
    if batch.state == types.BatchState.STATE_SUCCEEDED:
        # Retrieve output file
        output_uri = batch.output_uri
        if output_uri:
            client = genai.Client(api_key=apikey)
            file_content = client.files.get(name=output_uri).read()
            try:
                # Parse JSONL output
                results = [json.loads(line) for line in file_content.decode('utf-8').splitlines() if line.strip()]
                return results, True
            except json.JSONDecodeError as e:
                print(f"JSON decoding error: {e}")
                return None, False
    
    return None, False
