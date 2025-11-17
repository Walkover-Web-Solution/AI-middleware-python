from sqlalchemy import Column, String, Text, JSON, Enum, Integer, DateTime, Boolean, Float, ForeignKey,ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from models.postgres.pg_connection import Base

class Conversation(Base):
    __tablename__ = 'conversations'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    org_id = Column(String)
    thread_id = Column(String)
    model_name = Column(String)
    bridge_id = Column(String)
    message = Column(Text)
    message_by = Column(String)
    function = Column(JSON)
    type = Column(Enum('chat', 'completion', 'embedding', name='enum_conversations_type'), nullable=False)
    createdAt = Column(DateTime, default=func.now())
    updatedAt = Column(DateTime, default=func.now(), onupdate=func.now())
    chatbot_message = Column(Text)
    is_reset = Column(Boolean, default=False)
    tools_call_data = Column(ARRAY(JSON))
    user_feedback = Column(Integer)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    version_id = Column(String)
    sub_thread_id = Column(String, nullable=True)
    revised_prompt = Column(Text, nullable=True)
    image_urls = Column(ARRAY(JSON), nullable=True)
    urls = Column(ARRAY(String), nullable=True)
    AiConfig = Column(JSON, nullable=True)
    annotations = Column(ARRAY(JSON), nullable=True)
    fallback_model = Column(String, nullable=True)

class RawData(Base):
    __tablename__ = 'raw_data'
    __table_args__ = {'extend_existing': True}


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    org_id = Column(String)
    authkey_name = Column(String)
    latency = Column(Float)
    service = Column(String)
    status = Column(Boolean, nullable=False)
    error = Column(Text, default='none')
    model = Column(String)
    input_tokens = Column(Float)
    output_tokens = Column(Float)
    expected_cost = Column(Float)
    created_at = Column(DateTime, default=func.now())
    chat_id = Column(Integer, ForeignKey('conversations.id'))
    message_id = Column(UUID(as_uuid=True), nullable=True)
    variables = Column(JSON)
    is_present = Column(Boolean, default=False)
    firstAttemptError = Column(Text,  nullable=True)
    # conversation = relationship("Conversation", back_populates="raw_data")
    finish_reason = Column(String, nullable=True)

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

class ConversationLog(Base):
    __tablename__ = 'conversation_logs'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    llm_message = Column(Text, nullable=True)
    user = Column(Text, nullable=True)
    chatbot_message = Column(Text, nullable=True)
    updated_llm_message = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    user_feedback = Column(Integer, nullable=True, default=0)
    tools_call_data = Column(JSON, nullable=True, default=[])
    message_id = Column(String, nullable=True)
    sub_thread_id = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)
    version_id = Column(String, nullable=True)
    bridge_id = Column(String, nullable=True)
    image_urls = Column(JSON, nullable=True, default=[])
    urls = Column(JSON, nullable=True, default=[])
    AiConfig = Column(JSON, nullable=True)
    fallback_model = Column(JSON, nullable=True)
    org_id = Column(String, nullable=True)
    service = Column(String, nullable=True)
    model = Column(String, nullable=True)
    status = Column(Boolean, nullable=True, default=False)
    tokens = Column(JSON, nullable=True)
    variables = Column(JSON, nullable=True)
    latency = Column(JSON, nullable=True)
    firstAttemptError = Column(Text, nullable=True)
    finish_reason = Column(String, nullable=True)
    parent_id = Column(String, nullable=True)
    child_id = Column(String, nullable=True)
    prompt = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())