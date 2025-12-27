import json
import io
import httpx
import certifi
from openai import AsyncOpenAI

async def create_batch_file(data, apiKey):
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
        print("Error in create_batch_file:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise

async def process_batch_file(batch_input_file, apiKey):
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
        print(f"Error in process_batch_file: {e}")
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
        print(f"Error in retrieve_batch_status: {e}")
        raise
