from fastapi import Depends, HTTPException
from fastapi.requests import Request
from validations.validation import ChatCompletionRequest
from pydantic import ValidationError
from typing import Dict, Any, List,Union

def get_human_readable_error(exc: Union[ValidationError, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Convert validation errors to human-readable format.
    Handles both Pydantic ValidationError and raw error lists.
    """
    # Get errors list from either source
    errors_list = exc.errors() if isinstance(exc, ValidationError) else exc
    
    errors: List[Dict[str, Any]] = []
    
    for error in errors_list:
        loc = error.get('loc', ())
        field = '.'.join(str(l) for l in loc if l != '__root__') or 'root'
        msg = error.get('msg', 'Invalid value')
        errors.append({
            'message': msg,
            'type': error.get('type', 'validation_error')
        })
    
    return {
        "error": {
            "message": "Validation failed",
            "details": errors,
            "suggestion": "Please check your input values"
        }
    }

async def validate_request_data(request: Request):
    try:
        # Validate request body against Pydantic model
        body = await request.json()
        validated_data = ChatCompletionRequest(**body)  # Validate the body with the Pydantic model
        return validated_data
    except ValidationError as ve:
        # If validation error occurs, format the errors in a human-readable way
        error_response = get_human_readable_error(ve.errors())
        raise HTTPException(status_code=400, detail=error_response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request data: {e}")
