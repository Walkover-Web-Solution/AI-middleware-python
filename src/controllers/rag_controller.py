import requests
import re
from ..services.rag_services.chunking_methords import semantic_chunking, manual_chunking, recursive_chunking
from pinecone import Pinecone, ServerlessSpec
import uuid
from config import Config
from models.mongo_connection import db

rag_model = db["rag_data"]
rag_parent_model = db["rag_parent_data"]
# Initialize Pinecone with the API key
pc = Pinecone(api_key=Config.PINECONE_APIKEY)

pinecone_index = "ai-middleware"  # Ensure the index name is lowercase
# if not pc.index_exists(index_name):
#     try:
#         pinecone_index = pc.create_index(
#             name=index_name,
#             dimension=1536,
#             metric='cosine',
#             spec=ServerlessSpec(
#                 cloud="aws",
#                 region="us-east-1"
#             )  
#         )
#     except Exception as e:
#         print(f"Error creating Pinecone index: {e}")
#         raise
# else:
#     pinecone_index = pc.get_index(index_name)

async def create_vectors(request):
    try:
        # Extract the document ID from the URL
        body = await request.json()
        org_id = '1234' or request.state.profile.get("org", {}).get("id", "")
        url = body.get('doc_url')
        chunking_type = body.get('chunking_type') or 'manual'
        chunk_size = body.get('chunk_size') or '1000'
        chunk_overlap = body.get('chunk_overlap') or '200'
        name = body.get('name')
        description = body.get('description')
        if name is None or description is None:
            raise ValueError("Name and description are required.")
        data = await get_google_docs_data(url)
        text = data.get('data')
        doc_id = data.get('doc_id')
        if chunking_type == 'semantic':
            chunks, embeddings = await semantic_chunking(text=text)
        elif chunking_type == 'manual': 
            chunks, embeddings = await manual_chunking(text=text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif chunking_type == 'recursive': 
            chunks, embeddings = await recursive_chunking(text=text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        else:
            raise ValueError("Invalid chunking type or method not supported.")
        
        return await store_in_pinecone_and_mongo(embeddings, chunks, org_id, doc_id, name, description)
       
    except Exception as e:
        print(f"Error in create_vectors: {e}")
        raise

async def get_google_docs_data(url):
    try:
        doc_id = re.search(r'/d/(.*?)/', url).group(1)
        
        # Construct the Google Docs export URL (export as plain text)
        doc_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        
        # Send GET request to fetch the document content
        response = requests.get(doc_url)
        
        # Check if the request was successful
        if response.status_code == 200:
            return {
                "status": "success",
                "data": response.text,
                "doc_id": doc_id
            }
        else:
            raise Exception(f"Error fetching the document. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error in get_google_docs_data: {e}")
        raise

async def store_in_pinecone_and_mongo(embeddings, chunks, org_id, doc_id, name, description):
    try:
        index = pc.Index(pinecone_index)
        chunks_array = []
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        for embedding, chunk in zip(embeddings, chunks):
            chunk_id = str(uuid.uuid4())
            # Store in Pinecone
            vectors = [{
                "id": chunk_id,
                "values": embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding)),
                "metadata": {"org_id": org_id, "doc_id": doc_id}
            }]
            index.upsert(vectors=vectors, namespace=org_id)
            # Store in MongoDB
            rag_model.insert_one({
                "chunk": chunk,
                "chunk_id": chunk_id,
                "org_id": org_id,
                "doc_id": doc_id
            })
            chunks_array.append(chunk_id)
        rag_parent_model.insert_one({
            "name" : name,
            "description" : description,
            "doc_id" : doc_id,
            "org_id" : org_id,
            "chunks_id_array" : chunks_array
        })
        return {
            "success": True,
            "message": "Data stored successfully in Pinecone and MongoDB.",
            "doc_id": doc_id
        }
            
    except Exception as e:
        print(f"Error storing data in Pinecone or MongoDB: {e}")
        raise