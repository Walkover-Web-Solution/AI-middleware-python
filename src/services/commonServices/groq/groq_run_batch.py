import json
import io
from groq import AsyncGroq
import httpx
import certifi
import asyncio


async def create_batch_file(data, apiKey):
    """
    Creates a JSONL file and uploads it to Groq's Files API.
    
    Args:
        data: List of JSON strings (JSONL entries)
        apiKey: Groq API key
        
    Returns:
        Uploaded file object from Groq Files API
    """
    try:
        # Initialize Groq client
        groq_client = AsyncGroq(api_key=apiKey)
        
        # Create JSONL file content
        file_content = "\n".join(data)
        filelike_obj = io.BytesIO(file_content.encode("utf-8"))
        filelike_obj.name = "batch.jsonl"
        filelike_obj.seek(0)
        
        # Upload the JSONL file to Groq Files API
        batch_input_file = await groq_client.files.create(
            file=filelike_obj,
            purpose="batch"
        )
        
        print(f"Created Groq batch file: {batch_input_file.id}")
        return batch_input_file
        
    except Exception as e:
        print("Error in Groq create_batch_file:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise


async def process_batch_file(batch_input_file, apiKey):
    """
    Creates a batch job using the uploaded file.
    
    Args:
        batch_input_file: File object from create_batch_file
        apiKey: Groq API key
        
    Returns:
        Batch job object
    """
    try:
        # Initialize Groq client
        groq_client = AsyncGroq(api_key=apiKey)
        
        batch_input_file_id = batch_input_file.id
        
        # Create batch job with the uploaded file
        result = await groq_client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        print(f"Created Groq batch: {result.id}")
        return result
        
    except Exception as e:
        print(f"Error in Groq process_batch_file: {e}")
        raise


async def retrieve_batch_status(batch_id, apiKey):
    """
    Retrieves the status of a batch job.
    
    Args:
        batch_id: Batch job ID
        apiKey: Groq API key
        
    Returns:
        Batch job object with current status
    """
    try:
        # Initialize Groq client
        groq_client = AsyncGroq(api_key=apiKey)
        
        # Get batch status
        batch = await groq_client.batches.retrieve(batch_id)
        print(f"Groq batch status: {batch.status}")
        return batch
        
    except Exception as e:
        print(f"Error in Groq retrieve_batch_status: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping):
    """
    Handle Groq batch processing - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: Groq API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        Tuple of (results, is_completed)
    """
    batch = await retrieve_batch_status(batch_id, apikey)
    
    if batch.status == 'completed':
        file = batch.output_file_id or batch.error_file_id
        if file:
            # Create httpx client
            limits = httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            )
            
            http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                transport=httpx.AsyncHTTPTransport(
                    retries=3,
                    verify=certifi.where()
                ),
                limits=limits,
                follow_redirects=True
            )
            
            try:
                # Initialize Groq client with http_client
                groq_client = AsyncGroq(api_key=apikey, http_client=http_client)
                
                file_response = await groq_client.files.content(file)
                file_content = await asyncio.to_thread(file_response.read)
                try:
                    results = [json.loads(line) for line in file_content.decode('utf-8').splitlines() if line.strip()]
                    return results, True
                except json.JSONDecodeError as e:
                    print(f"JSON decoding error: {e}")
                    return None, False
            finally:
                await http_client.aclose()
    
    return None, False
