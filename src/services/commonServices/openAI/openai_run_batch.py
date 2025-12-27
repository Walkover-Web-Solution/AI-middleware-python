import json
import io
import httpx
import certifi
from openai import AsyncOpenAI

async def create_batch_file(data, apiKey, base_url=None):
    try:
        file_content = "\n".join(data)
        filelike_obj = io.BytesIO(file_content.encode("utf-8"))
        filelike_obj.name = "batch.jsonl"  # important for multipart metadata
        filelike_obj.seek(0)

        limits = httpx.Limits(
            max_keepalive_connections=5,
            max_connections=10,
            keepalive_expiry=30.0
        )

        timeout = httpx.Timeout(60.0, connect=10.0)

        http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            verify=certifi.where(),  # ✅ put verify here
            transport=httpx.AsyncHTTPTransport(retries=3),  # ✅ retries here only
        )

        try:
            # Use custom base_url if provided (for Groq, etc.)
            if base_url:
                openAI = AsyncOpenAI(api_key=apiKey, base_url=base_url, http_client=http_client)
            else:
                openAI = AsyncOpenAI(api_key=apiKey, http_client=http_client)
            
            batch_input_file = await openAI.files.create(
                file=filelike_obj,
                purpose="batch"
            )
            return batch_input_file
        finally:
            await http_client.aclose()
    except Exception as e:
        # More useful debug than just {e}
        print("Error in OpenAI create_batch_file:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise

async def process_batch_file(batch_input_file, apiKey, base_url=None):
    try:
        batch_input_file_id = batch_input_file.id
        
        # Create httpx client with proper production configuration
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
            # Use custom base_url if provided (for Groq, etc.)
            if base_url:
                openAI = AsyncOpenAI(api_key=apiKey, base_url=base_url, http_client=http_client)
            else:
                openAI = AsyncOpenAI(api_key=apiKey, http_client=http_client)
            
            result = await openAI.batches.create(
                input_file_id=batch_input_file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            print(result)
            return result
        finally:
            await http_client.aclose()
    except Exception as e:
        print(f"Error in OpenAI process_batch_file: {e}")
        raise


async def retrieve_batch_status(batch_id, apiKey):
    try:
        # Create httpx client with proper production configuration
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
            openAI = AsyncOpenAI(api_key=apiKey, http_client=http_client)
            batch = await openAI.batches.retrieve(batch_id)
            print(batch)
            return batch
        finally:
            await http_client.aclose()
    except Exception as e:
        print(f"Error in OpenAI retrieve_batch_status: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping, base_url=None):
    """
    Handle OpenAI-compatible batch processing (OpenAI, Groq) - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        base_url: Optional base URL for Groq or other OpenAI-compatible services
        
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
                import asyncio
                if base_url:
                    openAI = AsyncOpenAI(api_key=apikey, base_url=base_url, http_client=http_client)
                else:
                    openAI = AsyncOpenAI(api_key=apikey, http_client=http_client)
                
                file_response = await openAI.files.content(file)
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
