from pydantic import BaseModel
from typing import Optional, Dict,List,Any
from datetime import datetime

class internal_parameter_model(BaseModel):
    description: Optional[str]
    type: str
    enum: Optional[List[Any]]
    required_params: Optional[List[str]]
    parameter: Dict[str, 'internal_parameter_model'] = {}

    
class internal_fields_model(BaseModel):
    description: Optional[str]
    type: str
    enum: Optional[List[Any]]
    required_params: Optional[List[str]]
    parameter: Optional[Dict[str, internal_parameter_model]]
    
class data_to_update_model(BaseModel):
    bridge_ids: Optional[List[str]]=[]
    created_at: datetime
    description: str
    endpoint_name: Optional[str]
    fields: Dict[str, internal_fields_model]
    function_name: str
    org_id: str
    required_params: Optional[List[str]]=[]
    updated_at: datetime
    version: str
    
class update_tool_call_body_data(BaseModel):
    data_to_update : object
