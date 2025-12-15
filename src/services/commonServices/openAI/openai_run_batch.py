import os
import tempfile
import asyncio
import httpx
import traceback
from openai import OpenAI, APIConnectionError, APIError

async def create_batch_file(data, apiKey):
    temp_file_path = None
    try:
        # Create a temporary file to store the batch input
        file_content = "\n".join(data)
        
        # Write to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        # Use synchronous client in thread pool
        def upload_file():
            # Create a custom httpx client with proper configuration
            http_client = httpx.Client(
                timeout=60.0,
                transport=httpx.HTTPTransport(retries=3)
            )
            
            try:
                client = OpenAI(
                    api_key=apiKey,
                    http_client=http_client,
                    max_retries=0
                )
                with open(temp_file_path, 'rb') as f:
                    return client.files.create(
                        file=f,
                        purpose="batch"
                    )
            finally:
                http_client.close()
        
        # Run the synchronous call in a thread pool
        batch_input_file = await asyncio.to_thread(upload_file)
        return batch_input_file
        
    except APIConnectionError as e:
        print(f"Connection error in create_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to connect to OpenAI API: {str(e)}")
    except APIError as e:
        print(f"API error in create_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in create_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary file {temp_file_path}: {e}")

async def process_batch_file(batch_input_file, apiKey):
    try:
        batch_input_file_id = batch_input_file.id
        
        # Use synchronous client in thread pool
        def create_batch():
            http_client = httpx.Client(
                timeout=60.0,
                transport=httpx.HTTPTransport(retries=3)
            )
            
            try:
                client = OpenAI(
                    api_key=apiKey,
                    http_client=http_client,
                    max_retries=0
                )
                return client.batches.create(
                    input_file_id=batch_input_file_id,
                    endpoint="/v1/chat/completions",
                    completion_window="24h"
                )
            finally:
                http_client.close()
        
        # Run the synchronous call in a thread pool
        result = await asyncio.to_thread(create_batch)
        print(result)
        return result
        
    except APIConnectionError as e:
        print(f"Connection error in process_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to connect to OpenAI API: {str(e)}")
    except APIError as e:
        print(f"API error in process_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in process_batch_file: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise


async def retrieve_batch_status(batch_id, apiKey):
    try:
        # Use synchronous client in thread pool
        def get_batch():
            http_client = httpx.Client(
                timeout=60.0,
                transport=httpx.HTTPTransport(retries=3)
            )
            
            try:
                client = OpenAI(
                    api_key=apiKey,
                    http_client=http_client,
                    max_retries=0
                )
                return client.batches.retrieve(batch_id)
            finally:
                http_client.close()
        
        # Run the synchronous call in a thread pool
        batch = await asyncio.to_thread(get_batch)
        print(batch)
        return batch
        
    except APIConnectionError as e:
        print(f"Connection error in retrieve_batch_status: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"Failed to connect to OpenAI API: {str(e)}")
    except APIError as e:
        print(f"API error in retrieve_batch_status: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error in retrieve_batch_status: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise
