from sqlalchemy import Column, String, Text, JSON, Enum, Integer, DateTime, Boolean, Float, ForeignKey,ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from models.postgres.pg_connection import Base

class Conversation(Base):
    __tablename__ = 'agent_conversations'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    org_id = Column(String)
    thread_id = Column(String)
    bridge_id = Column(String)
    user_message = Column(Text)
    response = Column(Text)
    chatbot_response = Column(Text)
    tools_call_data = Column(JSON)
    user_feedback = Column(Integer)
    response_id = Column(UUID(as_uuid=True), nullable=True)
    version_id = Column(String)
    sub_thread_id = Column(String, nullable=True)
    revised_response = Column(Text, nullable=True)
    image_urls = Column(JSON, nullable=True)
    urls = Column(JSON, nullable=True)
    fallback_model = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    status = Column(Integer, nullable=True)  # 0: failed, 1: success, 2: second time is high
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    authkey_name = Column(String)
    latency = Column(Float)
    service = Column(String)
    tokens = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    message_id = Column(UUID(as_uuid=True), nullable=True)
    variables = Column(JSON)
    finish_reason = Column(String, nullable=True)
    model_name = Column(String)
    type = Column(String, nullable=False)
    AiConfig = Column(JSON, nullable=True)
    annotations = Column(JSON, nullable=True)

class system_prompt_versionings(Base):
    __tablename__ = 'system_prompt_versionings'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    system_prompt = Column(Text, nullable=False)
    bridge_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)

class user_bridge_config_history(Base):
    __tablename__ = 'user_bridge_config_history'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    org_id = Column(String, nullable=False)
    bridge_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    time = Column(DateTime, nullable=False, default=func.now())
    version_id = Column(String, nullable=True, default="")

class OrchestratorHistory(Base):
    __tablename__ = 'orchestrator_history'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(String, nullable=False)
    thread_id = Column(String, nullable=False)
    sub_thread_id = Column(String, nullable=False)
    model_name = Column(JSON, nullable=False)  # {"bridge_id": "model_name"}
    orchestrator_id = Column(String, nullable=False)
    user = Column(JSON, nullable=False)  # {"bridge_id": [user_messages]}
    response = Column(JSON, nullable=True)  # {"bridge_id": response_json}
    tool_call_data = Column(JSON, nullable=True)  # {"bridge_id": tool_call_json}
    createdAt = Column(DateTime, nullable=False, default=func.now())
    latency = Column(JSON, nullable=True)  # {"bridge_id": latency_json}
    tokens = Column(JSON, nullable=True)  # {"bridge_id": tokens_json}
    error = Column(JSON, nullable=True)  # {"bridge_id": error_json}
    variables = Column(JSON, nullable=True)  # {"bridge_id": variables_json}
    image_urls = Column(ARRAY(JSON), nullable=True)  # {"bridge_id": [image_urls]}
    ai_config = Column(JSON, nullable=True)  # {"bridge_id": ai_config_json}