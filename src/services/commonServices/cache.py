import os
import redis
import numpy as np
import joblib
import json
import hashlib
import warnings
from typing import Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from concurrent.futures import ThreadPoolExecutor
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance
)
import uuid
import asyncio
from datetime import datetime
from config import Config 

# Suppress sklearn warnings for clean output
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
warnings.filterwarnings("ignore", category=UserWarning, module="joblib")

# Load models with fallback for missing files
try:
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(script_dir, "model_for_classification")
    
    # Load classification model (LightGBM)
    model_path = os.path.join(model_dir, "classifier_model.joblib")
    model = joblib.load(model_path)
    
    # Load embedder for classification only
    model_name = "all-MiniLM-L6-v2"
    embedder = SentenceTransformer(model_name)
    
    # Load sentence-transformer for semantic embeddings
    semantic_model = embedder
    
    MODELS_LOADED = True
    print("="*20 + "MODELS LOADED SUCCESSFULLY" + "="*20)
except Exception as e:
    print(f"Failed to load models: {str(e)}")
    model = None
    embedder = None
    semantic_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fallback to SentenceTransformer
    MODELS_LOADED = True
    
    # Import sentence-transformers for fallback embedding
    try:
        semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        MODELS_LOADED = True  # At least we have embeddings
    except Exception:
        pass

# Classification and embedding functions
def sync_classify_prompt(prompt: str) -> str:
    """Synchronously classify prompt as personal or generic using TF-IDF or fallback logic"""
    try:
        if MODELS_LOADED and embedder is not None and model is not None:
            # Use TF-IDF for classification (as trained)
            vec = embedder.encode([prompt])
            prediction = model.predict(vec)[0]
            return "personal" if prediction == "personal" else "generic"
        else:
            # Fallback: Simple keyword-based classification for testing
            personal_keywords = ['my', 'me', 'i', 'mine', 'personal', 'favorite', 'prefer']
            prompt_lower = prompt.lower()
            if any(keyword in prompt_lower for keyword in personal_keywords):
                return "personal"
            return "generic"
    except Exception as e:
        return "personal"  # Default to generic on error

def sync_embed_prompt(prompt: str) -> np.ndarray:
    """Synchronously generate semantic embedding for prompt using sentence-transformers or fallback"""
    try:
        if semantic_model is not None:
            # Use sentence-transformers for semantic similarity
            embedding = semantic_model.encode([prompt])[0]
            return embedding
        else:
            # Fallback: Create a deterministic hash-based embedding for testing
            # This is much faster than downloading sentence-transformers models
            hash_obj = hashlib.md5(prompt.encode())
            hash_bytes = hash_obj.digest()
            
            # Create a 384-dimensional vector from the hash
            # Repeat the 16-byte hash to fill 384 dimensions (384/16 = 24 repetitions)
            embedding = np.tile(np.frombuffer(hash_bytes, dtype=np.uint8), 24)[:384]
            # Normalize to [0, 1] range
            embedding = embedding.astype(np.float32) / 255.0
            return embedding
    except Exception as e:
        # Ultimate fallback: random embedding
        return np.random.random(384).astype(np.float32)

async def classify_prompt(prompt: str) -> str:
    """Asynchronously classify prompt"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_classify_prompt, prompt)

async def embed_prompt(prompt: str) -> np.ndarray:
    """Asynchronously generate embedding for prompt"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, sync_embed_prompt, prompt)

def is_question(text: str) -> bool:
    #check if a string is a qeustion
    text = text.strip()
    
    # Check if it ends with a question mark
    if text.endswith("?"):
        return True

    # Check if it starts with a common question word
    question_words = (
        "who", "what", "when", "where", "why", "how",
        "is", "are", "can", "do", "does", "did",
        "will", "would", "should", "could", "am",
        "have", "has", "had", "shall", "may", "might"
    )
    words = text.lower().split()
    if words and words[0] in question_words:
        return True

    return False
# Redis setup (DB 0 = global/generic only)
global_cache = redis.Redis(
    host=Config.REDIS_HOST or "localhost", 
    port=int(Config.REDIS_PORT or 6379),
    db=int(Config.REDIS_DB or 0),
    decode_responses=True
)

class TwoLevelCache:
    """Two-level caching system using Qdrant for vector similarity and Redis for response storage"""
    
    def __init__(self, 
                 qdrant_host: str = Config.QDRANT_HOST, 
                 qdrant_port: int=Config.QDRANT_PORT,
                 similarity_threshold: float=Config.SIMILARITY_THRESHOLD,
                 cache_ttl_days: int=Config.CACHE_TTL_DAYS):
        """
        Initialize the two-level cache system
        
        Args:
            qdrant_host: Qdrant server host
            qdrant_port: Qdrant server port
            similarity_threshold: Minimum similarity score for cache hit
            cache_ttl_days: TTL for cached responses in days (default: 30 days)
        """


        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.similarity_threshold = similarity_threshold
        
        # Ensure TTL is a valid integer
        try:
            self.cache_ttl_seconds = int(cache_ttl_days) * 24 * 60 * 60  # Convert days to seconds
            if self.cache_ttl_seconds <= 0:
                self.cache_ttl_seconds = 30 * 24 * 60 * 60  # Default to 30 days
        except (ValueError, TypeError):
            print(f"Warning: Invalid cache_ttl_days value: {cache_ttl_days}. Using default 30 days.")
            self.cache_ttl_seconds = 30 * 24 * 60 * 60  # Default to 30 days
        
        # Collection name 
        self.generic_collection = Config.COLLECTION_NAME
        
        # Flag to track if collections are initialized
        self._collections_initialized = False

    def _check_connections(self) -> bool:
        """Simple connection check for Redis and Qdrant - only called when processing prompts"""
        try:
            # Test Redis connection
            global_cache.ping()
            # Test Qdrant connection
            self.qdrant_client.get_collections()
            return True
        except Exception:
            return False

    async def _initialize_collections(self):
        """Initialize Qdrant collection for storing embeddings - only generic prompts"""
        try:
            # Get vector dimension from sentence-transformers (384 for all-MiniLM-L6-v2)
            sample_embedding = sync_embed_prompt("test")
            vector_size = len(sample_embedding)
            
            # Only initialize generic collection
            try:
                # Check if collection exists
                collection_info = self.qdrant_client.get_collection(self.generic_collection)
            except Exception:
                # Create collection if it doesn't exist
                self.qdrant_client.create_collection(
                    collection_name=self.generic_collection,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                    
        except Exception as e:
            pass
        finally:
            self._collections_initialized = True
    
    async def _ensure_collections_initialized(self):
        """Ensure collections are initialized before operations"""
        if not self._collections_initialized:
            await self._initialize_collections()
    
    def _generate_cache_key(self, prompt: str, prompt_type: str) -> str:
        """Generate a unique cache key for the prompt"""
        key_data = f"{prompt}:{prompt_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_redis_client(self, prompt_type: str) -> redis.Redis:
        """Get Redis client - only generic prompts are cached"""
        if prompt_type == "personal":
            raise ValueError("Personal prompts are not cached")
        return global_cache
    
    def _get_collection_name(self, prompt_type: str) -> str:
        """Get Qdrant collection name"""
        if prompt_type == "personal":
            raise ValueError("Personal prompts are not cached")
        return self.generic_collection
    
    def _is_successful_response(self, response) -> bool:
        """Check if LLM response is successful and should be stored in cache"""
        try:
            # If response is a dictionary (LLM format)
            if isinstance(response, dict):
                # Check for success field
                if 'success' in response:
                    return response.get('success', False)
                
                # Check for error indicators
                if 'error' in response or 'Error' in str(response):
                    return False
                
                # Check if response has valid data
                if 'response' in response and 'data' in response['response']:
                    data = response['response']['data']
                    if isinstance(data, dict) and data.get('message'):
                        return True
                elif 'modelResponse' in response and 'data' in response['modelResponse']:
                    data = response['modelResponse']['data']
                    if isinstance(data, dict) and data.get('message'):
                        return True
                
                # If it's a valid dict but no clear structure, assume success
                return True
            
            # If response is a string
            elif isinstance(response, str):
                # Check for error keywords
                error_keywords = ['error', 'Error', 'ERROR', 'failed', 'Failed', 'FAILED']
                if any(keyword in response for keyword in error_keywords):
                    return False
                # Non-empty string responses are considered successful
                return len(response.strip()) > 0
            
            # For other types, assume unsuccessful
            else:
                return False
                
        except Exception as e:
            print(f"Error validating response success: {e}")
            return False
    
    async def search_similar_prompt(self, 
                                   embedding: np.ndarray, 
                                   prompt_type: str,
                                   limit: int = 5) -> Optional[Dict[str, Any]]:
        """Search for similar prompts in Qdrant vector database"""
        try:
            # Only handle generic prompts
            if prompt_type == "personal":
                return None
            
            # Ensure collections are initialized
            await self._ensure_collections_initialized()
            
            collection_name = self._get_collection_name(prompt_type)
            
            # Filter for generic prompts only
            search_filter = {
                "must": [
                    {
                        "key": "prompt_type",
                        "match": {
                            "value": "generic"
                        }
                    }
                ]
            }
            
            # Search for similar vectors
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=embedding.tolist(),
                query_filter=search_filter,
                limit=limit,
                score_threshold=self.similarity_threshold
            )

            if search_results:
                # Check each result to ensure Redis entry still exists
                redis_client = self._get_redis_client(prompt_type)
                
                for i, result in enumerate(search_results):
                    cache_key = result.payload.get("cache_key")
                    
                    # Only generic prompts are processed
                    if cache_key and redis_client.exists(cache_key):
                        # Found valid match with existing Redis entry
                        return {
                            "cache_key": cache_key,
                            "score": result.score,
                            "original_prompt": result.payload.get("prompt")
                        }
                    elif cache_key:
                        # Found orphaned embedding - delete it
                        try:
                            self.qdrant_client.delete(
                                collection_name=collection_name,
                                points_selector=[result.id]
                            )
                        except Exception as e:
                            pass  # Ignore deletion errors
                
                # No valid matches found (all were orphaned)
            
            return None
            
        except Exception as e:
            return None
    
    async def get_cached_response(self, cache_key: str, prompt_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached response from Redis and reset TTL on access"""
        try:
            redis_client = self._get_redis_client(prompt_type)
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                response_data = json.loads(cached_data)
                
                # Reset TTL to 1 month when response is accessed
                redis_client.expire(cache_key, self.cache_ttl_seconds)
                
                # Update access timestamp in the cached data
                response_data["last_accessed"] = datetime.now().isoformat()
                redis_client.setex(cache_key, self.cache_ttl_seconds, json.dumps(response_data))
                
                return response_data
            
            return None
            
        except Exception as e:
            return None
    
    async def store_prompt_and_response(self, 
                                       prompt: str, 
                                       embedding: np.ndarray,
                                       response,  # Can be dict or str
                                       prompt_type: str) -> bool:
        """Store prompt embedding in Qdrant and response in Redis"""
        try:
            # Only store generic prompts 
            if prompt_type == "personal":
                return False  # Personal prompts are not stored
            
            # Ensure collections are initialized
            await self._ensure_collections_initialized()

            embed_task = asyncio.create_task(embed_prompt(prompt))
            embedding = await embed_task
            
            cache_key = self._generate_cache_key(prompt, prompt_type)
            
            # Store response in Redis (only generic)
            redis_client = self._get_redis_client(prompt_type)
            response_data = {
                "response": response,
                "prompt": prompt,
                "prompt_type": prompt_type,
                "timestamp": datetime.now().isoformat()
            }
            
            # Store response with TTL - validate TTL value first
            ttl_value = int(self.cache_ttl_seconds)
            if ttl_value <= 0 or ttl_value > (365 * 24 * 60 * 60):  # Max 1 year
                ttl_value = 30 * 24 * 60 * 60  # Default to 30 days
                
            try:
                redis_client.setex(
                    cache_key, 
                    ttl_value,
                    json.dumps(response_data)
                )
            except redis.exceptions.ResponseError as e:
                print(f"Redis setex error: {e}. TTL value: {ttl_value}, Key: {cache_key[:50]}...")
                raise
            
            # Store embedding in Qdrant (only generic)
            collection_name = self._get_collection_name(prompt_type)
            point_payload = {
                "cache_key": cache_key,
                "prompt": prompt,
                "prompt_type": prompt_type,
                "timestamp": datetime.now().isoformat()
            }
            
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload=point_payload
            )
            
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            print(f"Error storing prompt and response: {str(e)}")
            import traceback
            print(f"Storage error traceback: {traceback.format_exc()}")
            return False
    
    async def process_prompt_with_cache(self, 
                                       prompt: str,
                                       llm_function = None,
                                       clean_db: str = None) -> Dict[str, Any]:
        """Main method to process a prompt with two-level caching : Personal prompts always call LLM"""
        try:
            # If clean_db is provided, clear the specified database first
            if clean_db in ['redis', 'qdrant', 'all']:
                await self.clear_database(clean_db)
                return {
                    "response": f"Cleared {clean_db}",
                    "_cache_info": {
                        "source": "error",
                        "prompt_type": "unknown"
                    }
                }

            # Check database connections first
            if not self._check_connections():
                return {
                    "response": "Error: Database connections not available (Redis/Qdrant)",
                    "_cache_info": {
                        "source": "error",
                        "prompt_type": "unknown"
                    }
                }
            # Step 1: Classify and embed prompt in parallel
            classify_task = asyncio.create_task(classify_prompt(prompt))
            embed_task = asyncio.create_task(embed_prompt(prompt))
            
            prompt_type = await classify_task
            embedding = await embed_task
            
            # MODIFICATION: If prompt is personal, skip cache and call LLM directly
            # Personal prompts are NOT stored or retrieved from cache at all
            if prompt_type == "personal":
                # Call LLM directly for personal prompts
                if llm_function:
                    # Handle both sync and async LLM functions
                    if asyncio.iscoroutinefunction(llm_function):
                        llm_response = await llm_function()
                    else:
                        llm_response = llm_function()
                    
                    # Ensure response is in the expected format with _cache_info
                    if isinstance(llm_response, str):
                        return {
                            "response": llm_response,
                            "_cache_info": {
                                "source": "llm",
                                "prompt_type": prompt_type
                            }
                        }
                    elif isinstance(llm_response, dict):
                        llm_response['_cache_info'] = {
                            "source": "llm",
                            "prompt_type": prompt_type
                        }
                        return llm_response
                    else:
                        return {
                            "response": str(llm_response),
                            "_cache_info": {
                                "source": "llm",
                                "prompt_type": prompt_type
                            }
                        }
                else:
                    return {
                        "response": "No LLM function provided",
                        "_cache_info": {
                            "source": "error",
                            "prompt_type": prompt_type
                        }
                    }
            
            # For generic prompts, use normal caching logic
            # Step 2: Search for similar prompts in vector database
            similar_prompt = await self.search_similar_prompt(
                embedding=embedding,
                prompt_type=prompt_type
            )
            
            cached_response = None
            if similar_prompt:
                # Step 3: Try to get cached response
                cached_response = await self.get_cached_response(
                    cache_key=similar_prompt["cache_key"],
                    prompt_type=prompt_type
                )
                    
            if cached_response:
                # Cache hit - return cached response in test-compatible format
                cached_llm_response = cached_response.get("response",[])
                
                # Return cached response in LLM-compatible format
                if isinstance(cached_llm_response, dict) and 'success' in cached_llm_response:
                    # Cached response is already in LLM format, add cache metadata
                    cached_llm_response['_cache_info'] = {
                        "source": "cache",
                        "prompt_type": prompt_type,
                        "similarity_score": similar_prompt["score"],
                        "original_prompt": similar_prompt["original_prompt"]
                    }
                    return cached_llm_response
                else:
                    # Convert cached response to LLM-compatible format
                    message = str(cached_llm_response)
                    return {
                        "success": True,
                        "response": {
                            "data": {
                                "message": message,
                                "cached": True
                            }
                        },
                        "modelResponse": {
                            "data": {
                                "message": message,
                                "cached": True
                            }
                        },
                        "_cache_info": {
                            "source": "cache",
                            "prompt_type": prompt_type,
                            "similarity_score": similar_prompt["score"],
                            "original_prompt": similar_prompt["original_prompt"]
                        }
                    }
        
            # Step 4: Cache miss - call LLM function
            if llm_function:
                # Handle both sync and async LLM functions
                if asyncio.iscoroutinefunction(llm_function):
                    llm_response = await llm_function(prompt)
                else:
                    llm_response = llm_function(prompt)
            else:
                return {
                    "response": "No LLM function provided",
                    "source": "error",
                    "prompt_type": prompt_type
                }
        
            # Step 5: Store response asynchronously in background (only if successful)
            if self._is_successful_response(llm_response) and llm_response:
                asyncio.create_task(self._store_async(
                    prompt=prompt,
                    embedding=embedding,
                    response=llm_response,
                    prompt_type=prompt_type
                ))
            else:
                print(f"⚠️ Skipping storage for unsuccessful response: {str(llm_response)[:100]}...")
        
            # Step 6: Return response with cache metadata (no datetime)
            if isinstance(llm_response, dict):
                llm_response['_cache_info'] = {
                    "source": "llm",
                    "prompt_type": prompt_type
                }
                return llm_response
            else:
                # If LLM returns a string, wrap it in the expected format
                return {
                    "response": llm_response,
                    "source": "llm",
                    "prompt_type": prompt_type
                }
            
        except Exception as e:
            return {
                "response": f"Error processing prompt: {str(e)}",
                "_cache_info":{
                    "source": "error",
                    "prompt_type": prompt_type
                }
            }
    
    async def _store_async(self, 
                          prompt: str, 
                          embedding: np.ndarray,
                          response,  # Can be dict or str
                          prompt_type: str):
        """Store prompt and response asynchronously in background"""
        try:
            answer = ''
            if isinstance(response,dict):
                answer = response.get('response',{}).get('data',{}).get('content',{}) if response.get('response',{}).get('data',{}).get('content',{}) else response['response']['data']['content']
            if isinstance(answer, str) and is_question(answer):
                print("Response not stored since a question.")
                return
            success = await self.store_prompt_and_response(
                prompt=prompt,
                embedding=embedding,
                response=response,
                prompt_type=prompt_type
            )
            if success:
                print(f"✅ Successfully stored cache for prompt: {prompt[:50]}...")
            else:
                print(f"❌ Failed to store cache for prompt: {prompt[:50]}...")
        except Exception as e:
            print(f"❌ Error in background storage task: {str(e)}")
            import traceback
            print(f"Background storage error traceback: {traceback.format_exc()}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            await self._ensure_collections_initialized()
            
            # Get Qdrant collection stats
            generic_info = self.qdrant_client.get_collection(self.generic_collection)
            
            # Get Redis stats
            generic_redis_info = global_cache.info()
            
            return {
                "qdrant": {
                    "generic_collection": {
                        "points_count": generic_info.points_count,
                        "vectors_count": generic_info.vectors_count
                    }
                },
                "redis": {
                    "generic_db": {
                        "keys_count": generic_redis_info.get("db0", {}).get("keys", 0),
                        "memory_usage": generic_redis_info.get("used_memory_human", "0B")
                    }
                },
                "note": "Only generic prompts are cached. Personal prompts are not stored or retrieved."
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def cleanup_orphaned_embeddings(self, batch_size: int = 100) -> int:
        """Clean up orphaned embeddings in Qdrant that don't have corresponding Redis entries"""
        try:
            await self._ensure_collections_initialized()
            
            cleaned_count = 0
            collections = [self.generic_collection, self.personal_collection]
            
            for collection_name in collections:
                prompt_type = "personal" if collection_name == self.personal_collection else "generic"
                redis_client = self._get_redis_client(prompt_type)
                
                # Get all points in batches
                offset = None
                while True:
                    # Scroll through points
                    points, next_offset = self.qdrant_client.scroll(
                        collection_name=collection_name,
                        limit=batch_size,
                        offset=offset,
                        with_payload=True
                    )
                    
                    if not points:
                        break
                    
                    # Check each point
                    orphaned_ids = []
                    for point in points:
                        cache_key = point.payload.get("cache_key")
                        if cache_key and not redis_client.exists(cache_key):
                            orphaned_ids.append(point.id)
                    
                    # Delete orphaned points
                    if orphaned_ids:
                        self.qdrant_client.delete(
                            collection_name=collection_name,
                            points_selector=orphaned_ids
                        )
                        cleaned_count += len(orphaned_ids)
                    
                    # Update offset for next batch
                    offset = next_offset
                    if offset is None:
                        break
            
            return cleaned_count
            
        except Exception as e:
            return 0
    
    async def delete_cache_entry(self, cache_key: str, prompt_type: str) -> bool:
        """Manually delete a specific cache entry from both Redis and Qdrant"""
        try:
            # Delete from Redis
            redis_client = self._get_redis_client(prompt_type)
            redis_deleted = redis_client.delete(cache_key) > 0
            
            # Find and delete from Qdrant
            collection_name = self._get_collection_name(prompt_type)
            
            # Search for points with this cache_key
            search_results = self.qdrant_client.scroll(
                collection_name=collection_name,
                scroll_filter={
                    "must": [
                        {
                            "key": "cache_key",
                            "match": {
                                "value": cache_key
                            }
                        }
                    ]
                },
                limit=10,
                with_payload=True
            )
            
            points_to_delete = [point.id for point in search_results[0]]
            qdrant_deleted = False
            
            if points_to_delete:
                self.qdrant_client.delete(
                    collection_name=collection_name,
                    points_selector=points_to_delete
                )
                qdrant_deleted = True
            
            return redis_deleted or qdrant_deleted
            
        except Exception as e:
            return False
    
    async def clear_database(self, db_name: str = "all") -> Dict[str, bool]:
        """Clear database(s)
        
        Args:
            db_name: Name of database to clear. Options:
                    - 'redis': Clear Redis DB 0 (generic cache)
                    - 'qdrant': Clear Qdrant generic_prompts collection
                    - 'all': Clear all databases (default)
        
        Note: only caches generic prompts. Personal prompts bypass cache entirely.
        
        Returns:
            Dict with status of each clear operation
        """
        results = {
            "redis": False,
            "qdrant": False
        }
        
        try:
            # Clear Redis database (only global/generic)
            if db_name in ["redis", "all"]:
                try:
                    global_cache.flushdb()
                    results["redis"] = True
                except Exception as e:
                    print(f"Error clearing Redis global cache: {e}")
            
            # Clear Qdrant collection (only generic)
            if db_name in ["qdrant", "all"]:
                try:
                    # Ensure collections are initialized first
                    await self._ensure_collections_initialized()
                    
                    # Delete the entire collection and recreate it
                    try:
                        self.qdrant_client.delete_collection(self.generic_collection)
                    except Exception:
                        pass  # Collection might not exist
                    
                    # Recreate the collection
                    sample_embedding = sync_embed_prompt("test")
                    vector_size = len(sample_embedding)
                    
                    self.qdrant_client.create_collection(
                        collection_name=self.generic_collection,
                        vectors_config=VectorParams(
                            size=vector_size,
                            distance=Distance.COSINE
                        )
                    )
                    results["qdrant"] = True
                except Exception as e:
                    print(f"Error clearing Qdrant generic collection: {e}")
            
            # Inform user about unsupported operations
            unsupported_ops = ["redis_personal", "qdrant_personal", "redis_all", "qdrant_all"]
            if db_name in unsupported_ops:
                print(f"!'{db_name}' not supported - only generic prompts are cached")
            
            # Print summary
            cleared_dbs = [db for db, status in results.items() if status]
            if cleared_dbs:
                print(f"✅ Successfully cleared: {', '.join(cleared_dbs)}")
            else:
                print("❌ No databases were cleared")
            
            return results
            
        except Exception as e:
            print(f"Error in clear_database: {e}")
            return results

# Initialize the cache system
cache_system = TwoLevelCache()

# Convenience function for easy integration
async def process_prompt_with_cache(prompt: str, llm_function = None, clean_db: str = None) -> Dict[str, Any]:
    """Convenience function to process prompts with caching"""
    return await cache_system.process_prompt_with_cache(prompt, llm_function)
