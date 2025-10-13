import json
import uuid
import traceback
from datetime import datetime, timezone
from models.index import combined_models
from sqlalchemy import and_
from globals import *

postgres = combined_models['pg']

class UnifiedConversationService:
    """
    Service for managing unified conversations that combine conversation and raw data
    """
    
    @staticmethod
    async def create_unified_conversation(
        org_id: str,
        thread_id: str,
        bridge_id: str,
        user_message: str,
        response: str,
        chatbot_response: str,
        model_name: str,
        service: str,
        type: str,
        version_id: str = None,
        sub_thread_id: str = None,
        tools_call_data: list = None,
        image_urls: list = None,
        urls: list = None,
        AiConfig: dict = None,
        annotations: list = None,
        fallback_model: str = None,
        authkey_name: str = None,
        latency: float = None,
        input_tokens: float = None,
        output_tokens: float = None,
        expected_cost: float = None,
        variables: dict = None,
        finish_reason: str = None,
        error: str = None,
        status: int = 1,  # 0: failed, 1: success, 2: second attempt success
        message_id: str = None,
        response_id: str = None,
        revised_response: str = None,
        user_feedback: int = None
    ):
        """
        Create a single unified conversation record
        """
        try:
            # Prepare tokens object
            tokens = {
                'input_tokens': input_tokens or 0,
                'output_tokens': output_tokens or 0,
                'expected_cost': expected_cost or 0
            }
            
            # Create unified conversation data
            unified_data = {
                'org_id': org_id,
                'thread_id': thread_id,
                'bridge_id': bridge_id,
                'user_message': user_message,
                'response': response,
                'chatbot_response': chatbot_response,
                'tools_call_data': tools_call_data or [],
                'user_feedback': user_feedback,
                'response_id': response_id,
                'version_id': version_id,
                'sub_thread_id': sub_thread_id,
                'revised_response': revised_response,
                'image_urls': image_urls or [],
                'urls': urls or [],
                'fallback_model': fallback_model,
                'error': error,
                'status': status,
                'authkey_name': authkey_name,
                'latency': latency or 0,
                'service': service,
                'tokens': tokens,
                'message_id': message_id,
                'variables': variables or {},
                'finish_reason': finish_reason,
                'model_name': model_name,
                'type': type,
                'AiConfig': AiConfig,
                'annotations': annotations or [],
                'createdAt': datetime.now(),
                'updatedAt': datetime.now(),
                'created_at': datetime.now()
            }
            
            # Insert into database
            session = postgres['session']()
            try:
                from models.postgres.pg_models import Conversation
                
                unified_conversation = Conversation(**unified_data)
                session.add(unified_conversation)
                session.commit()
                
                conversation_id = unified_conversation.id
                logger.info(f"Created unified conversation with ID: {conversation_id}")
                
                return conversation_id
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error in create_unified_conversation: {str(e)}")
                raise e
            finally:
                session.close()
                
        except Exception as error:
            logger.error(f"Error in create_unified_conversation: {str(error)}")
            logger.error(traceback.format_exc())
            raise error
    
    @staticmethod
    async def find_conversations(
        org_id: str,
        thread_id: str = None,
        bridge_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = None,
        offset: int = None
    ):
        """
        Find unified conversations with filters
        """
        try:
            session = postgres['session']()
            try:
                from models.postgres.pg_models import Conversation
                
                query = session.query(Conversation).filter(
                    Conversation.org_id == org_id
                )
                
                if thread_id:
                    query = query.filter(Conversation.thread_id == thread_id)
                
                if bridge_id:
                    query = query.filter(Conversation.bridge_id == bridge_id)
                
                if start_time and end_time:
                    query = query.filter(
                        and_(
                            Conversation.createdAt >= start_time,
                            Conversation.createdAt <= end_time
                        )
                    )
                
                if offset:
                    query = query.offset(offset)
                
                if limit:
                    query = query.limit(limit)
                
                query = query.order_by(Conversation.createdAt.desc())
                
                conversations = query.all()
                
                # Convert to dict format
                result = []
                for conv in conversations:
                    conv_dict = {
                        'id': conv.get('id'),
                        'org_id': conv.get('org_id'),
                        'thread_id': conv.get('thread_id'),
                        'bridge_id': conv.get('bridge_id'),
                        'user_message': conv.get('user_message'),
                        'response': conv.get('response'),
                        'chatbot_response': conv.get('chatbot_response'),
                        'tools_call_data': conv.get('tools_call_data'),
                        'user_feedback': conv.get('user_feedback'),
                        'response_id': conv.get('response_id'),
                        'version_id': conv.get('version_id'),
                        'sub_thread_id': conv.get('sub_thread_id'),
                        'revised_response': conv.get('revised_response'),
                        'image_urls': conv.get('image_urls'),
                        'urls': conv.get('urls'),
                        'fallback_model': conv.get('fallback_model'),
                        'error': conv.get('error'),
                        'status': conv.get('status'),
                        'authkey_name': conv.get('authkey_name'),
                        'latency': conv.get('latency'),
                        'service': conv.get('service'),
                        'tokens': conv.get('tokens'),
                        'message_id': conv.get('message_id'),
                        'variables': conv.get('variables'),
                        'finish_reason': conv.get('finish_reason'),
                        'model_name': conv.get('model_name'),
                        'type': conv.get('type'),
                        'AiConfig': conv.get('AiConfig'),
                        'annotations': conv.get('annotations'),
                        'createdAt': conv.get('createdAt'),
                        'updatedAt': conv.get('updatedAt'),
                        'created_at': conv.get('created_at')
                    }
                    result.append(conv_dict)
                
                return result
                
            finally:
                session.close()
                
        except Exception as error:
            logger.error(f"Error in find_conversations: {str(error)}")
            logger.error(traceback.format_exc())
            raise error
    
    @staticmethod
    async def find_by_id(conversation_id: int):
        """
        Find unified conversation by ID
        """
        try:
            session = postgres['session']()
            try:
                from models.postgres.pg_models import Conversation
                
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    return None
                
                # Convert to dict format
                conv_dict = {
                    'id': conversation.id,
                    'org_id': conversation.org_id,
                    'thread_id': conversation.thread_id,
                    'bridge_id': conversation.bridge_id,
                    'user_message': conversation.user_message,
                    'response': conversation.response,
                    'chatbot_response': conversation.chatbot_response,
                    'tools_call_data': conversation.tools_call_data,
                    'user_feedback': conversation.user_feedback,
                    'response_id': conversation.response_id,
                    'version_id': conversation.version_id,
                    'sub_thread_id': conversation.sub_thread_id,
                    'revised_response': conversation.revised_response,
                    'image_urls': conversation.image_urls,
                    'urls': conversation.urls,
                    'fallback_model': conversation.fallback_model,
                    'error': conversation.error,
                    'status': conversation.status,
                    'authkey_name': conversation.authkey_name,
                    'latency': conversation.latency,
                    'service': conversation.service,
                    'tokens': conversation.tokens,
                    'message_id': conversation.message_id,
                    'variables': conversation.variables,
                    'finish_reason': conversation.finish_reason,
                    'model_name': conversation.model_name,
                    'type': conversation.type,
                    'AiConfig': conversation.AiConfig,
                    'annotations': conversation.annotations,
                    'createdAt': conversation.createdAt,
                    'updatedAt': conversation.updatedAt,
                    'created_at': conversation.created_at
                }
                
                return conv_dict
                
            finally:
                session.close()
                
        except Exception as error:
            logger.error(f"Error in find_by_id: {str(error)}")
            logger.error(traceback.format_exc())
            raise error
    
    @staticmethod
    async def update_conversation(conversation_id: int, **kwargs):
        """
        Update unified conversation
        """
        try:
            session = postgres['session']()
            try:
                from models.postgres.pg_models import Conversation
                
                conversation = session.query(Conversation).filter(
                    Conversation.id == conversation_id
                ).first()
                
                if not conversation:
                    logger.warning(f"Conversation with ID {conversation_id} not found")
                    return None
                
                # Update fields
                for key, value in kwargs.items():
                    if hasattr(conversation, key):
                        setattr(conversation, key, value)
                
                conversation.updatedAt = datetime.now()
                
                session.commit()
                logger.info(f"Updated unified conversation with ID: {conversation_id}")
                
                return conversation_id
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error in update_conversation: {str(e)}")
                raise e
            finally:
                session.close()
                
        except Exception as error:
            logger.error(f"Error in update_conversation: {str(error)}")
            logger.error(traceback.format_exc())
            raise error
