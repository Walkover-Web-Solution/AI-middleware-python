import json
import httpx
import certifi


async def create_batch(requests_data, apiKey):
    """
    Create a batch job using AIML's native batch API.
    
    Args:
        requests_data: List of request objects, each containing 'custom_id' and 'params'
        apiKey: AIML API key
        
    Returns:
        Batch response object with id, status, created_at, etc.
    """
    try:
        # Create httpx client with proper production configuration
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
            verify=certifi.where(),
            transport=httpx.AsyncHTTPTransport(retries=3),
        )

        try:
            # AIML native batch API endpoint
            url = "https://api.aimlapi.com/v1/batches"
            
            headers = {
                "Authorization": f"Bearer {apiKey}",
                "Content-Type": "application/json"
            }
            
            # AIML expects a JSON body with 'requests' array
            payload = {
                "requests": requests_data
            }
            
            response = await http_client.post(url, json=payload, headers=headers)
            
            batch_result = response.json()
            
            return batch_result
        finally:
            await http_client.aclose()
    except Exception as e:
        print("Error in AIML create_batch:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise


async def retrieve_batch_status(batch_id, apiKey):
    """
    Retrieve the status or results of a specific batch.
    
    Args:
        batch_id: The ID of the batch to retrieve
        apiKey: AIML API key
        
    Returns:
        Batch status object or results (JSONL format if completed)
    """
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
            url = f"https://api.aimlapi.com/v1/batches?batch_id={batch_id}"
            
            headers = {
                "Authorization": f"Bearer {apiKey}"
            }
            
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()
            
            batch_status = response.json()
            print("AIML Batch status:", batch_status)
            
            return batch_status
        finally:
            await http_client.aclose()
    except Exception as e:
        print(f"Error in AIML retrieve_batch_status: {e}")
        raise


async def cancel_batch(batch_id, apiKey):
    """
    Cancel a specific batch job.
    
    Args:
        batch_id: The ID of the batch to cancel
        apiKey: AIML API key
        
    Returns:
        Cancellation response
    """
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
            url = f"https://api.aimlapi.com/v1/batches/cancel/{batch_id}"
            
            headers = {
                "Authorization": f"Bearer {apiKey}"
            }
            
            response = await http_client.post(url, headers=headers)
            response.raise_for_status()
            
            cancel_result = response.json()
            print("AIML Batch cancelled:", cancel_result)
            
            return cancel_result
        finally:
            await http_client.aclose()
    except Exception as e:
        print(f"Error in AIML cancel_batch: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping):
    """
    Handle AIML batch processing - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: AIML API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        Tuple of (formatted_results, is_completed)
    """
    batch_status = await retrieve_batch_status(batch_id, apikey)
    
    if batch_status.get("status") == "completed":
        # AIML returns results directly in the response
        results = batch_status.get("results", [])
        return results, True
    
    return None, False
