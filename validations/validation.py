from pydantic import BaseModel,Field,constr,conint,confloat,validator, ConfigDict,model_validator
from typing import Optional, Dict,List,Any,Literal

from typing_extensions import Annotated
from src.configs.model_configuration import model_config_document


        
# class ModelConfig(BaseModel):
#     model: str
#     creativity_level: Optional[float] = Field(None, ge=0, le=2)
#     max_tokens: Optional[int]
#     probability_cutoff: Optional[float] = Field(None, ge=0, le=1)
#     log_probability: Optional[bool]
#     repetition_penalty: Optional[float] = Field(None, ge=0, le=2)
#     novelty_penalty: Optional[float] = Field(None, ge=0, le=2)
#     response_count: Optional[int] = Field(None, ge=1)
#     additional_stop_sequences: Optional[str]
#     stream: Optional[bool]

# class Configurations(BaseModel):
#     model: Optional[str]
#     type: Optional[str]
#     prompt: Optional[str]
#     tools: Optional[object]
#     creativity_level: Annotated[float, Field(ge=0, le=2)]
#     probability_cutoff: Annotated[float, Field(ge=0, le=1)]
#     repetition_penalty: Annotated[float, Field(ge=0)]
#     novelty_penalty: Annotated[float, Field(ge=0)]
#     log_probability: bool
#     response_format: Dict[str, str]
#     response_count: conint(ge=1)
#     ResponseFormat: 
#     stop_sequences: str
#     token_selection_limit: conint(ge=1)
#     topP: confloat(ge=0, le=1)
#     input_text: str
#     echo_input: bool
#     best_of: conint(ge=1)
#     seed: Optional[int]
#     response_suffix: str
#     max_output_tokens : int

class Bridge_update(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slugName: Optional[str] = None
    service: Optional[str] = None
    bridgeType: Optional[str] = None
    configuration: Optional[object] = None
    apikey: Optional[str] = None
    name: Optional[str] = None
    apikey_object_id: Optional[str] = None
    functionData: Optional[object]
    
class ChatCompletionRequest(BaseModel):
    user: str = Field(..., description="User identifier")
    bridge_id: str = Field(..., description="Bridge identifier")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")
    model: Optional[str] = Field(None, description="Model name (required if configuration is provided)")
    response_type: Optional[Literal["text", "json_object"]] = Field(None, description="Response format")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Model-specific configuration")

    @model_validator(mode='before')
    def validate_configuration(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        configuration = data.get("configuration")
        model = data.get("model")

        # Skip validation if no configuration or no model
        if configuration is None or model is None:
            return data

        # Get model config (replace with your actual implementation)
        model_config = model_config_document.get(model)
        if not model_config:
            raise ValueError(f"Model '{model}' not found in configuration document")

        config_schema = model_config.get("configuration", {})
        
        for field_name, field_schema in config_schema.items():
            if field_name in configuration:
                cls._validate_field(
                    field_name=field_name,
                    field_schema=field_schema,
                    user_value=configuration[field_name]
                )

        return data

    @classmethod
    def _validate_field(cls, field_name: str, field_schema: Dict[str, Any], user_value: Any):
        """Validate a single configuration field against its schema"""
        field_type = field_schema.get("field")

        if field_type == "slider":
            if not isinstance(user_value, (int, float)):
                raise ValueError(f"{field_name} must be a number")
            if "min" in field_schema and user_value < field_schema["min"]:
                raise ValueError(f"{field_name} must be ≥ {field_schema['min']}")
            if "max" in field_schema and user_value > field_schema["max"]:
                raise ValueError(f"{field_name} must be ≤ {field_schema['max']}")

        elif field_type == "boolean":
            if not isinstance(user_value, bool):
                raise ValueError(f"{field_name} must be a boolean (True/False)")

        elif field_type == "dropdown":
            options = field_schema.get("options", [])
            if user_value not in options:
                raise ValueError(f"{field_name} must be one of: {options}")

        elif field_type == "number":
            if not isinstance(user_value, (int, float)):
                raise ValueError(f"{field_name} must be a number")

        elif field_type == "select":
            options = [opt["type"] for opt in field_schema.get("options", [])]
            if user_value not in options:
                raise ValueError(f"{field_name} must be one of: {options}")