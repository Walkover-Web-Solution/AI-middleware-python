import requests
import re
from ..services.rag_services.chunking_methords import semantic_chunking, manual_chunking, recursive_chunking
from pinecone import Pinecone
import uuid
from config import Config
from models.mongo_connection import db
from langchain_openai import OpenAIEmbeddings
from config import Config
from fastapi.responses import JSONResponse
from bson import ObjectId
from fastapi import HTTPException
from ..services.utils.rag_utils import extract_pdf_text, extract_csv_text, extract_docx_text
import traceback
from ..services.utils.rag_utils import get_csv_query_type

rag_model = db["rag_datas"]
rag_parent_model = db["rag_parent_datas"]
# Initialize Pinecone with the API key
pc = Pinecone(api_key=Config.PINECONE_APIKEY)

pinecone_index = Config.PINECONE_INDEX
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
        body = await request.form()
        file = body.get('file')
        file_extension = 'url'
        if file:
            file_extension = file.filename.split('.')[-1].lower()
            
            # Extract text based on file type
            if file_extension == 'pdf':
                text = await extract_pdf_text(file)
            # elif file_extension == 'docx':
            #     text = await extract_docx_text(file)
            elif file_extension == 'csv':
                text = await extract_csv_text(file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF, and CSV are supported.")
        org_id = request.state.profile.get("org", {}).get("id", "")
        user = request.state.profile.get("user", {})
        embed = request.state.embed
        url = body.get('doc_url')
        chunking_type = body.get('chunking_type') or 'recursive'
        chunk_size = int(body.get('chunk_size', 512))
        chunk_overlap = int(body.get('chunk_overlap', chunk_size*0.15))
        name = body.get('name')
        description = body.get('description')
        doc_id = None
        if name is None or description is None:
            raise HTTPException(status_code=400, detail="Name and description are required.")
        if url is not None:
            data = await get_google_docs_data(url)
            text = data.get('data')
            doc_id = data.get('doc_id')
        text = str(text)
        if chunking_type == 'semantic':
            chunks, embeddings = await semantic_chunking(text=text)
        elif chunking_type == 'manual': 
            chunks, embeddings = await manual_chunking(text=text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif chunking_type == 'recursive': 
            chunks, embeddings = await recursive_chunking(text=text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        else:
            raise HTTPException(status_code=400, detail="Invalid chunking type or method not supported.")
        return JSONResponse(
            status_code=200,
            content={
                "name" : name, 
                "description" : description,
                'type' : file_extension,
                **(await store_in_pinecone_and_mongo(embeddings, chunks, org_id, user['id'] if embed else None, name, description, doc_id, file_extension))
            }
        )

       
    except HTTPException as http_error:
        print(f"HTTP error in create_vectors: {http_error.detail}")
        raise http_error
    except Exception as error:
        traceback.print_exc()
        print(f"Error in create_vectors: {error}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

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
            raise HTTPException(status_code=500, detail=f"Error fetching the document. Status code: {response.status_code}")
    except Exception as error:
        print(f"Error in get_google_docs_data: {error}")
        raise HTTPException(status_code=500, detail= error)

async def store_in_pinecone_and_mongo(embeddings, chunks, org_id, user_id, name, description, doc_id, file_extension):
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
        result = await rag_parent_model.insert_one({
            "name": name,
            "description": description,
            "doc_id": doc_id,
            "org_id": org_id,
            "chunks_id_array": chunks_array,
            "user_id" : user_id if user_id else None,
            "type" : file_extension
        })
        inserted_id = result.inserted_id
        return {
            "success": True,
            "message": "Data stored successfully.",
            "doc_id": doc_id,
            "_id": str(inserted_id)
        }
            
    except Exception as error:
        print(f"Error storing data in Pinecone or MongoDB: {error}")
        raise HTTPException(status_code=500, detail= error)

async def get_vectors_and_text(request):
    try:
        body = await request.json()
        org_id = request.state.profile.get("org", {}).get("id", "")
        doc_id = body.get('doc_id')
        query = body.get('query')
        top_k = body.get('top_k', 2)
        
        if query is None:
            raise HTTPException(status_code=400, detail="Query is required.")
        
        text = await get_text_from_vectorsQuery({
            'Document_id': doc_id, 
            'query': query, 
            'org_id': org_id
        })
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "text": text['response']
        })
        
    except Exception as error:
        print(f"Error in get_vectors_and_text: {error}")
        raise HTTPException(status_code=400, detail=error)

async def get_all_docs(request):
    try:
        org_id = request.state.profile.get("org", {}).get("id", "")
        user_id = request.state.profile.get("user", {}).get('id')
        embed = request.state.embed
        result = await rag_parent_model.find({
            'org_id' : org_id, 
            'user_id' : user_id if embed else None
        }).to_list(length=None)
        
        for doc in result:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": result
        })

    except Exception as error:
        print(f"Error in get_all_docs: {error}")
        raise HTTPException(status_code=500, detail=error)

async def delete_doc(request):
    try:
        body = await request.json()
        index = pc.Index(pinecone_index)
        org_id = request.state.profile.get("org", {}).get("id", "")
        id = body.get('id')
        result = await rag_parent_model.find_one({
            '_id': ObjectId(id),
            'org_id': org_id
        })
        chunks_array = [] if result is None else result.get('chunks_id_array', [])
        
        for chunk_id in chunks_array:
            index.delete(ids=[chunk_id], namespace=org_id)
            rag_model.delete_one({"chunk_id": chunk_id})
        deleted_doc = await rag_parent_model.find_one_and_delete({"_id": ObjectId(id)})
        if deleted_doc:
            deleted_doc['_id'] = str(deleted_doc['_id'])
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": f"Deleted documents with chunk IDs: {chunks_array}.",
            "data": deleted_doc
        })
    except Exception as error:
        print(f"Error in delete_docs: {error}")
        raise HTTPException(status_code=500, detail = error)
    

async def get_text_from_vectorsQuery(args):
    try:
        doc_id = args.get('Document_id')
        query = args.get('query')
        org_id = args.get('org_id')
        top_k = args.get('top_k', 3)
        additional_query = {}
        
        if query is None:
            raise HTTPException(status_code=400, detail="Query is required.")
        
        doc_data = (await rag_parent_model.find({
            'org_id' : org_id, 
            '_id' : ObjectId(doc_id)
        }).to_list())[0]
        
        if not doc_data: 
            raise Exception("Invalid document id provided.")
        
        if doc_data['source']['fileFormat'] == 'csv': 
            to_search_for = await get_csv_query_type(doc_data, query)
            additional_query['chunkType'] = to_search_for
        
        embedding = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY).embed_documents([query])
        # Query Pinecone
        index = pc.Index(pinecone_index)
        
        query_response = index.query(
            vector=embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding)),
            namespace=org_id,
            filter={ "docId": doc_id, **additional_query },
            top_k = top_k  # Adjust the number of results as needed
        )
        query_response_ids = [result['id'] for result in query_response['matches']]
        
        # Query MongoDB using query_response_ids
        mongo_query = {"_id": {"$in": [ObjectId(id) for id in query_response_ids] }}
        cursor = rag_model.find(mongo_query)
        mongo_results = await cursor.to_list(length=None)
        text = ""
        for result in mongo_results:
            text += result.get('data', '')
        
        return {
            'response': text,
            'metadata': {
                'flowHitId': ''
            },
            'status': 1
        }
        
    except Exception as error:
        print(f"Error in get_vectors_and_text: {error}")
        raise {
            'response': str(error),
            'metadata': {
                'flowHitId': ''
            },
            'status': 1
        }