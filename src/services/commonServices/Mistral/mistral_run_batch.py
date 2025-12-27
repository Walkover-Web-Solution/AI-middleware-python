import json
import uuid
import tempfile
import os
from mistralai import Mistral

async def create_batch_file(batch_requests, apiKey):
    """
    Creates a JSONL file and uploads it to Mistral Files API.
    
    Args:
        batch_requests: List of JSON strings (JSONL entries)
        apiKey: Mistral API key
        
    Returns:
        Uploaded file object from Mistral Files API
    """
    try:
        # Initialize Mistral client
        client = Mistral(api_key=apiKey)
        
        # Create JSONL file content
        jsonl_content = "\n".join(batch_requests)
        
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(jsonl_content)
            temp_file_path = temp_file.name
        
        try:
            # Open file and read content, then close it before upload
            with open(temp_file_path, "rb") as f:
                file_content = f.read()
            
            # Upload the JSONL file to Mistral Files API
            uploaded_file = client.files.upload(
                file={
                    "file_name": f"batch-{uuid.uuid4()}.jsonl",
                    "content": file_content
                },
                purpose="batch"
            )
            return uploaded_file
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    except Exception as e:
        print("Error in Mistral create_batch_file:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise

async def process_batch_file(uploaded_file, apiKey, model):
    """
    Creates a batch job using the uploaded file.
    
    Args:
        uploaded_file: File object from create_batch_file
        apiKey: Mistral API key
        model: Model name to use for batch processing
        
    Returns:
        Batch job object
    """
    try:
        # Initialize Mistral client
        client = Mistral(api_key=apiKey)
        
        # Create batch job with the uploaded file
        batch_job = client.batch.jobs.create(
            input_files=[uploaded_file.id],
            model=model,
            endpoint="/v1/chat/completions",
            metadata={"source": "ai-middleware"}
        )
        print(f"Created Mistral batch job: {batch_job.id}")
        return batch_job
    except Exception as e:
        print(f"Error in Mistral process_batch_file: {e}")
        raise

async def retrieve_batch_status(batch_id, apiKey):
    """
    Retrieves the status of a batch job.
    
    Args:
        batch_id: Batch job ID
        apiKey: Mistral API key
        
    Returns:
        Batch job object with current status
    """
    try:
        # Initialize Mistral client
        client = Mistral(api_key=apiKey)
        
        # Get batch job status
        batch_job = client.batch.jobs.get(job_id=batch_id)
        print(f"Mistral batch status: {batch_job.status}")
        return batch_job
    except Exception as e:
        print(f"Error in Mistral retrieve_batch_status: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping):
    """
    Handle Mistral batch processing - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: Mistral API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        Tuple of (results, is_completed)
    """
    batch_job = await retrieve_batch_status(batch_id, apikey)
    
    if batch_job.status == "SUCCESS":
        # Download output file
        from mistralai import Mistral
        client = Mistral(api_key=apikey)
        output_file_stream = client.files.download(file_id=batch_job.output_file)
        file_content_bytes = output_file_stream.read()
        file_content_str = file_content_bytes.decode('utf-8')
        
        try:
            results = [json.loads(line) for line in file_content_str.splitlines() if line.strip()]
            return results, True
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
            return None, False
    
    return None, False
