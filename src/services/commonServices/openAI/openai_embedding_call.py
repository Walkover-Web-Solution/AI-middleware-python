from ..baseService.baseService import BaseService
from .openai_embedding_model import embedding_model

class OpenaiEmbedding(BaseService):
    async def execute_embedding(self):
        """Call the embedding model with the provided text input."""
        self.customConfig['input'] = self.text
        modelResponse = await embedding_model(self.customConfig, self.apikey)
        return modelResponse
    
        
        
