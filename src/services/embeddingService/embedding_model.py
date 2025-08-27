from sentence_transformers import SentenceTransformer
import concurrent.futures
import threading
from typing import List, Union

class embedding_model():

    # def __init__(self,model = "all-MiniLM-L12-V6"):
    #     self.model = SentenceTransformer(model)
    # EMBEDDING SIZE = 384  

    # def __init__(self,model = "avsolatorio/GIST-small-Embedding-1536"):
    #     self.model = SentenceTransformer(model)
    # Not working | personal repo needs token for access
    # EMBEDDING SIZE = 1536  


    # from InstructorEmbedding import INSTRUCTOR
    # def __init__(self,model = "hkunlp/instructor-xl"):
    #     self.model = INSTRUCTOR(model)
    # not working since requires 5 gb memory to run
    # EMBEDDING SIZE = 1536  

    # sentence tranformer mixedbread-ai/mxbai-embed-large-v1

    def __init__(self, model="BAAI/bge-large-en-v1.5"):
        self.model = SentenceTransformer(model)
        self._lock = threading.Lock()  # Thread safety for model access
    # EMBEDDING SIZE = 1024

    def create_embedding(self, query):
        """Create embedding for a single query"""
        if not query:
            return []
        
        with self._lock:  # Ensure thread-safe access to the model
            embeddings = self.model.encode(query)
        return embeddings

    def create_embeddings_batch(self, queries: List[str], max_workers: int = 4):
        """Create embeddings for multiple queries using multithreading"""
        if not queries:
            return []
        
        # Filter out empty queries
        valid_queries = [(i, query) for i, query in enumerate(queries) if query and query.strip()]
        
        if not valid_queries:
            return []
        
        # Use ThreadPoolExecutor for parallel processing
        embeddings_dict = {}
        
        def process_query(indexed_query):
            index, query = indexed_query
            try:
                with self._lock:  # Thread-safe model access
                    embedding = self.model.encode(query)
                return index, embedding
            except Exception as e:
                print(f"Error processing query at index {index}: {e}")
                return index, []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_query = {executor.submit(process_query, indexed_query): indexed_query 
                             for indexed_query in valid_queries}
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    index, embedding = future.result()
                    embeddings_dict[index] = embedding
                except Exception as e:
                    indexed_query = future_to_query[future]
                    print(f"Error processing query {indexed_query[1]}: {e}")
        
        # Return embeddings in original order
        embeddings = []
        for i, query in enumerate(queries):
            if i in embeddings_dict:
                embeddings.append(embeddings_dict[i])
            else:
                embeddings.append([])  # Empty embedding for failed/empty queries
        
        return embeddings

    async def create_embeddings_async(self, queries: List[str], max_workers: int = 4):
        """Async wrapper for batch embedding creation"""
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Run the synchronous batch processing in a thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            embeddings = await loop.run_in_executor(
                executor, 
                self.create_embeddings_batch, 
                queries, 
                max_workers
            )
        
        return embeddings