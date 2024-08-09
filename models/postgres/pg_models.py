from sqlalchemy import Column, String, Text, JSON, Enum, Integer, DateTime, Boolean, Float, ForeignKey
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

    # raw_data = relationship("RawData", back_populates="conversation")

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
    variables = Column(JSON)
    is_present = Column(Boolean, default=False)
    # conversation = relationship("Conversation", back_populates="raw_data")

class system_prompt_versionings(Base):
    __tablename__ = 'system_prompt_versionings'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    system_prompt = Column(Text, nullable=False)
    bridge_id = Column(String, nullable=False)
    org_id = Column(String, nullable=False)