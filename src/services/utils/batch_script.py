from ..cache_service import find_in_cache_with_prefix, delete_in_cache
from openai import AsyncOpenAI
from ..utils.send_error_webhook import create_response_format
from ..commonServices.baseService.baseService import sendResponse
import asyncio
import json
import httpx
import certifi
from .ai_middleware_format import  Batch_Response_formatter
from src.configs.constant import redis_keys
from globals import *

# Import service-specific batch handlers
from ..commonServices.openAI.openai_run_batch import handle_batch_results as openai_handle_batch
from ..commonServices.Mistral.mistral_run_batch import handle_batch_results as mistral_handle_batch
from ..commonServices.AiMl.aiml_run_batch import handle_batch_results as aiml_handle_batch
from ..commonServices.Google.gemini_run_batch import handle_batch_results as gemini_handle_batch
from ..commonServices.anthrophic.anthropic_run_batch import handle_batch_results as anthropic_handle_batch
from ..commonServices.groq.groq_run_batch import handle_batch_results as groq_handle_batch



async def repeat_function():
    while True:
        await check_batch_status()
        await asyncio.sleep(900)


async def process_batch_results(results, service, batch_id, batch_variables, custom_id_mapping):
    """
    Common function to process batch results for all services.
    
    Args:
        results: List of result items
        service: Service name (e.g., 'gemini_batch', 'anthropic_batch')
        batch_id: Batch ID
        batch_variables: Optional batch variables
        custom_id_mapping: Mapping of custom_id to index
        
    Returns:
        List of formatted results
    """
    formatted_results = []
    
    for index, result_item in enumerate(results):
        # Extract custom_id and result data (format varies by service)
        if service == 'gemini':
            custom_id = result_item.get("key", None)
            result_data = result_item.get("response", {})
            result_data["key"] = custom_id
        elif service == 'anthropic':
            custom_id = result_item.get("custom_id", None)
            result_data = result_item.get("result", {})
        elif service in ['openai', 'groq', 'ai_ml']:
            custom_id = result_item.get("custom_id", None)
            response = result_item.get("response", {})
            result_data = response.get("body", {})
            status_code = response.get("status_code", 200)
        elif service == 'mistral':
            custom_id = result_item.get("custom_id", None)
            result_data = result_item.get("response", {})
        else:
            custom_id = result_item.get("custom_id", None)
            result_data = result_item
        
        # Check for errors
        has_error = False
        if service in ['openai', 'groq']:
            has_error = status_code >= 400 or "error" in result_data
        elif service == 'anthropic':
            has_error = result_data.get("type") == "error"
        else:
            has_error = "error" in result_data
        
        if has_error:
            formatted_content = {
                "custom_id": custom_id,
                "batch_id": batch_id,
                "error": result_data.get("error", result_data),
                "status_code": status_code if service in ['openai', 'groq'] else 400
            }
        else:
            # Format successful response
            if service == 'anthropic':
                # For Anthropic, extract the message from result
                result_data = result_data.get("message", {})
            
            formatted_content = await Batch_Response_formatter(
                response=result_data,
                service=service,
                tools={},
                type='chat',
                images=None,
                batch_id=batch_id,
                custom_id=custom_id,
                isBatch=True
            )
        
        # Add batch_variables to response if available
        if batch_variables is not None and custom_id in custom_id_mapping:
            variable_index = custom_id_mapping[custom_id]
            if variable_index < len(batch_variables):
                formatted_content["variables"] = batch_variables[variable_index]
        
        formatted_results.append(formatted_content)
    
    return formatted_results


# Service handler mapping
SERVICE_HANDLERS = {
    'gemini': ('gemini', gemini_handle_batch),
    'anthropic': ('anthropic', anthropic_handle_batch),
    'openai': ('openai', lambda bid, key, bv, cm: openai_handle_batch(bid, key, bv, cm)),
    'groq': ('groq', groq_handle_batch),
    'mistral': ('mistral', mistral_handle_batch),
    'ai_ml': ('ai_ml', aiml_handle_batch),
}


async def check_batch_status():
    try:
        print("Batch Script running...")
        batch_ids = await find_in_cache_with_prefix('batch_')
        if batch_ids is None:
            return
        
        for batch_data in batch_ids:
            apikey = batch_data.get('apikey')
            webhook = batch_data.get('webhook')
            batch_id = batch_data.get('id')
            batch_variables = batch_data.get('batch_variables')
            custom_id_mapping = batch_data.get('custom_id_mapping', {})
            service = batch_data.get('service')
            
            if webhook.get('url') is not None:
                response_format = create_response_format(webhook.get('url'), webhook.get('headers'))
            
            try:
                # Get the appropriate handler for this service
                handler_info = SERVICE_HANDLERS.get(service)
                
                if handler_info:
                    service_name, handler = handler_info
                    
                    # Call the service-specific handler
                    results, is_completed = await handler(
                        batch_id, apikey, batch_variables, custom_id_mapping
                    )
                    
                    if is_completed and results:
                        # Process and format the results
                        formatted_results = await process_batch_results(
                            results, service_name, batch_id, batch_variables, custom_id_mapping
                        )
                        
                        # Check if all responses are errors
                        has_success = any(
                            item.get("status_code") is None or item.get("status_code", 200) < 400 
                            for item in formatted_results
                        )
                        
                        await sendResponse(response_format, data=formatted_results, success=has_success)
                        
                        # Delete from cache
                        cache_key = f"{redis_keys['batch_']}{batch_id}"
                        await delete_in_cache(cache_key)
                else:
                    logger.error(f"Unknown service type: {service}")
                    
            except Exception as error:
                logger.error(f"Error processing batch {batch_id}: {str(error)}")

    except Exception as error:
        logger.error(f"An error occurred while checking the batch status: {str(error)}")
