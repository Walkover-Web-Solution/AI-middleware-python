from models.postgres.pg_connection import Session
from models.postgres.pg_models import OrchestratorHistory
from src.services.utils.logger import logger
from datetime import datetime
from typing import Dict, Optional
import json

class OrchestratorHistoryService:
    """Service for managing orchestrator history in PostgreSQL"""
    
    @staticmethod
    async def save_orchestrator_history(data: Dict) -> Optional[int]:
        """
        Save orchestrator history to PostgreSQL
        
        Args:
            data: Dictionary containing orchestrator history data
            
        Returns:
            Integer ID of created record or None if failed
        """
        session = Session()
        try:
            # Create new orchestrator history record
            orchestrator_record = OrchestratorHistory(
                org_id=data.get('org_id'),
                thread_id=data.get('thread_id'),
                sub_thread_id=data.get('sub_thread_id', data.get('thread_id')),
                model_name=data.get('model_name', {}),
                orchestrator_id=data.get('orchestrator_id'),
                user=data.get('user', {}),
                response=data.get('response', {}),
                tool_call_data=data.get('tool_call_data', {}),
                latency=data.get('latency', {}),
                tokens=data.get('tokens', {}),
                error=data.get('error', {}),
                variables=data.get('variables', {}),
                image_urls=data.get('image_urls', {}),
                ai_config=data.get('ai_config', {})
            )
            
            session.add(orchestrator_record)
            session.commit()
            
            record_id = orchestrator_record.id
            logger.info(f"Orchestrator history saved with ID: {record_id}")
            return record_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving orchestrator history: {str(e)}")
            return None
        finally:
            session.close()

# Global object to store orchestrator data by bridge_id during execution
class OrchestratorDataCollector:
    """Global collector for orchestrator data during execution"""
    
    def __init__(self):
        self._data = {}
    
    def initialize_session(self, thread_id: str, org_id: str, orchestrator_id: str):
        """Initialize a new orchestrator session"""
        if thread_id not in self._data:
            self._data[thread_id] = {
                'org_id': org_id,
                'thread_id': thread_id,
                'sub_thread_id': thread_id,
                'orchestrator_id': orchestrator_id,
                'model_name': {},
                'user': {},
                'response': {},
                'tool_call_data': {},
                'latency': {},
                'tokens': {},
                'error': {},
                'variables': {},
                'image_urls': {},
                'ai_config': {}
            }
    
    def add_bridge_data(self, thread_id: str, bridge_id: str, data: Dict):
        """Add data for a specific bridge_id"""
        if thread_id not in self._data:
            logger.warning(f"Thread {thread_id} not initialized in orchestrator collector")
            return
        
        session_data = self._data[thread_id]
        
        # Store data by bridge_id
        if 'model_name' in data:
            session_data['model_name'][bridge_id] = data['model_name']
        
        if 'user' in data:
            session_data['user'][bridge_id] = data['user']
        
        if 'response' in data:
            session_data['response'][bridge_id] = data['response']
        
        if 'tool_call_data' in data:
            session_data['tool_call_data'][bridge_id] = data['tool_call_data']
        
        if 'latency' in data:
            session_data['latency'][bridge_id] = data['latency']
        
        if 'tokens' in data:
            session_data['tokens'][bridge_id] = data['tokens']
        
        if 'error' in data:
            session_data['error'][bridge_id] = data['error']
        
        if 'variables' in data:
            session_data['variables'][bridge_id] = data['variables']
        
        if 'image_urls' in data:
            session_data['image_urls'][bridge_id] = data['image_urls']
        
        if 'ai_config' in data:
            session_data['ai_config'][bridge_id] = data['ai_config']
    
    def get_session_data(self, thread_id: str) -> Optional[Dict]:
        """Get all collected data for a thread"""
        return self._data.get(thread_id)
    
    def clear_session(self, thread_id: str):
        """Clear data for a specific thread"""
        if thread_id in self._data:
            del self._data[thread_id]
    
    def get_all_sessions(self) -> Dict:
        """Get all active sessions (for debugging)"""
        return self._data


# Global instance
orchestrator_collector = OrchestratorDataCollector()
