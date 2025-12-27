import json
import uuid
from anthropic import Anthropic

async def create_batch_requests(batch_requests, apiKey, model):
    """
    Creates and submits a message batch to Anthropic API.
    
    Args:
        batch_requests: List of request dictionaries
        apiKey: Anthropic API key
        model: Model name to use
        
    Returns:
        Message batch object from Anthropic API
    """
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=apiKey)
        
        # Create message batch
        message_batch = client.messages.batches.create(
            requests=batch_requests
        )
        
        print(f"Created Anthropic batch: {message_batch.id}")
        return message_batch
        
    except Exception as e:
        print("Error in Anthropic create_batch_requests:", repr(e))
        print("Cause:", repr(getattr(e, "__cause__", None)))
        raise

async def retrieve_batch_status(batch_id, apiKey):
    """
    Retrieves the status of an Anthropic message batch.
    
    Args:
        batch_id: Message batch ID
        apiKey: Anthropic API key
        
    Returns:
        Message batch object with current status
    """
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=apiKey)
        
        # Get batch status
        message_batch = client.messages.batches.retrieve(batch_id)
        print(f"Anthropic batch status: {message_batch.processing_status}")
        return message_batch
        
    except Exception as e:
        print(f"Error in Anthropic retrieve_batch_status: {e}")
        raise

async def retrieve_batch_results(batch_id, apiKey):
    """
    Retrieves the results of a completed Anthropic message batch.
    
    Args:
        batch_id: Message batch ID
        apiKey: Anthropic API key
        
    Returns:
        List of batch results
    """
    try:
        # Initialize Anthropic client
        client = Anthropic(api_key=apiKey)
        
        # Iterate through results
        results = []
        for result in client.messages.batches.results(batch_id):
            results.append(result)
        
        print(f"Retrieved {len(results)} results from Anthropic batch {batch_id}")
        return results
        
    except Exception as e:
        print(f"Error in Anthropic retrieve_batch_results: {e}")
        raise


async def handle_batch_results(batch_id, apikey, batch_variables, custom_id_mapping):
    """
    Handle Anthropic batch processing - retrieve status and process results.
    
    Args:
        batch_id: Batch ID
        apikey: Anthropic API key
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        Tuple of (results, is_completed)
    """
    message_batch = await retrieve_batch_status(batch_id, apikey)
    
    if message_batch.processing_status == "ended":
        # Retrieve batch results
        results = await retrieve_batch_results(batch_id, apikey)
        results_list = [result.model_dump() for result in results]
        return results_list, True
    
    return None, False
