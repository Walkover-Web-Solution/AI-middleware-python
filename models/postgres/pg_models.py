from sqlalchemy import Column, String, Text, JSON, Enum, Integer, DateTime, Boolean, Float, ForeignKey,ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
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

# Single Table Approach - Better for User Isolation
class RagVectorStore(Base):
    __tablename__ = 'rag_vector_store'
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    
    # Namespace-like fields (similar to Pinecone)
    namespace = Column(String, nullable=False)  # Format: "org_id:user_id" or just "org_id"
    org_id = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    
    # Document metadata (embedded in same table)
    doc_id = Column(String, nullable=False)
    doc_name = Column(String, nullable=False)
    doc_description = Column(Text)
    doc_type = Column(String, nullable=False)  # file extension or 'url'
    
    # Chunk data
    chunk_id = Column(String, nullable=False, unique=True)
    chunk_data = Column(Text, nullable=False)
    chunk_type = Column(String, nullable=True)  # for CSV query types
    chunk_index = Column(Integer, nullable=False)  # Order within document
    
    # Vector embedding
    embedding = Column(Vector(1536))  # OpenAI text-embedding-3-small dimension
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Placeholder models for imports (not used in single-table approach)
class RagDocument:
    pass

class RagChunk:
    pass