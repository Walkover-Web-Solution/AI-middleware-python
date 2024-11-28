from pydantic import BaseModel
from typing import Any, Optional
from fastapi import HTTPException,status
from fastapi.responses import JSONResponse

# Response model to standardize all API responses
class ResponseModel(BaseModel):
    status_code: int
    success: bool
    message: Optional[str] | None = None
    data: Optional[Any] | None = None

def Json_response(status_code: int,success: bool, message: str, data: Optional[Any] = None):
    response_data = ResponseModel(
        status_code=status_code,
        success=success,
        message=message,
        data=data #jaisa tum bhejo waise jaiga
    )
    return JSONResponse(
        status_code=status_code,
        content=response_data.model_dump() 
    )
# Function to raise HTTPException with standardized response format
def raise_http_exception(status_code: int, message: str, data: Optional[Any] = None):
    raise HTTPException(
        status_code= status.HTTP_400_BAD_REQUEST,
        detail=ResponseModel(
            status_code=status_code,
            success=False,
            message=message,
            data=data
        ).model_dump()
    )
