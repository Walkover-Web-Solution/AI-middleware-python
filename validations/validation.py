from pydantic import BaseModel,Field,constr,conint,confloat,validator, ConfigDict
from typing import Optional, Dict,List,Any

from typing_extensions import Annotated


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
    