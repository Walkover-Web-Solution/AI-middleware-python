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
from models.postgres.pg_connection import Session
from models.postgres.pg_models import RagDocument, RagChunk, RagVectorStore
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

rag_model = db["rag_datas"]
rag_parent_model = db["rag_parent_datas"]
# Initialize Pinecone with the API key
pc = Pinecone(api_key=Config.PINECONE_APIKEY)

pinecone_index = Config.PINECONE_INDEX
index = pc.Index(pinecone_index)

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
        
        if query is None and doc_id is None:
            raise HTTPException(status_code=400, detail="Query and Doc_id required.")
        text = await get_text_from_vectorsQuery({
            'Document_id': doc_id, 
            'query': query, 
            'org_id': org_id,
            'top_k': top_k
        })
        
        # Check if the operation was successful based on status
        success = text.get('status') == 1
        status_code = 200 if success else 400
        
        return JSONResponse(status_code=status_code, content={
            "success": success,
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
        
        doc_data = await rag_parent_model.find_one({
            '_id' : ObjectId(doc_id)
        })
        
        if not doc_data: 
            raise Exception("Invalid document id provided.")
        
        if doc_data['source']['fileFormat'] == 'csv': 
            to_search_for = await get_csv_query_type(doc_data, query)
            additional_query['chunkType'] = to_search_for
        
        embedding = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY, model="text-embedding-3-small").embed_documents([query])
        # Query Pinecone
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
        # Create a dictionary to map id to pos so that we can maintain order in mongo results.
        id_to_position = {id: pos for pos, id in enumerate(query_response_ids)}
        
        mongo_results = await cursor.to_list(length=None)
        mongo_results.sort(key=lambda x: id_to_position.get(str(x.get('_id')), float('inf')))
        
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
        print(f"Error in get_text_from_vectorsQuery: {error}")
        return {
            'response': str(error),
            'metadata': {
                'flowHitId': ''
            },
            'status': 0  # 0 indicates error/failure
        }

# Single Table PgVector Implementation - Better User Isolation

def create_namespace(org_id: str, user_id: str = None) -> str:
    """Create namespace string for org isolation (like Pinecone namespaces)"""
    return org_id

async def create_vectors_single_table(request):
    """Create vectors and store in single PgVector table with namespace isolation"""
    try:
        # Extract the document data
        body = await request.form()
        file = body.get('file')
        file_extension = 'url'
        if file:
            file_extension = file.filename.split('.')[-1].lower()
            
            # Extract text based on file type
            if file_extension == 'pdf':
                text = await extract_pdf_text(file)
            elif file_extension == 'csv':
                text = await extract_csv_text(file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and CSV are supported.")
        
        org_id = request.state.profile.get("org", {}).get("id", "")
        user = request.state.profile.get("user", {})
        embed = request.state.embed
        user_id = user['id'] if embed else None
        url = body.get('doc_url')
        chunking_type = body.get('chunking_type') or 'recursive'
        chunk_size = int(body.get('chunk_size', 512))
        chunk_overlap = int(body.get('chunk_overlap', chunk_size*0.15))
        name = body.get('name')
        description = body.get('description')
        doc_id = None
        text = ""  # Initialize text variable
        
        # Set default values if not provided
        if name is None:
            if file:
                name = f"Document_{file.filename.split('.')[0]}_{str(uuid.uuid4())[:8]}"
            elif url:
                name = f"GoogleDoc_{str(uuid.uuid4())[:8]}"
            else:
                name = f"Document_{str(uuid.uuid4())[:8]}"
        
        if description is None:
            description = f"Auto-generated description for {name}"
        
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
                "name": name, 
                "description": description,
                'type': file_extension,
                **(await store_in_single_table(embeddings, chunks, org_id, user_id, name, description, doc_id, file_extension))
            }
        )

    except HTTPException as http_error:
        print(f"HTTP error in create_vectors_single_table: {http_error.detail}")
        raise http_error
    except Exception as error:
        traceback.print_exc()
        print(f"Error in create_vectors_single_table: {error}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

async def store_in_single_table(embeddings, chunks, org_id, user_id, name, description, doc_id, file_extension):
    """Store embeddings and chunks in single table with namespace isolation"""
    session = Session()
    try:
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        # Create namespace for org isolation
        namespace = create_namespace(org_id)
        
        # Store all chunks in single table
        for chunk_index, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
            chunk_id = str(uuid.uuid4())
            
            # Prepare embedding vector
            embedding_vector = embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding))
            
            rag_entry = RagVectorStore(
                namespace=namespace,
                org_id=org_id,
                user_id=user_id,
                doc_id=doc_id,
                doc_name=name,
                doc_description=description,
                doc_type=file_extension,
                chunk_id=chunk_id,
                chunk_data=chunk,
                chunk_index=chunk_index,
                embedding=embedding_vector
            )
            session.add(rag_entry)
        
        session.commit()
        
        return {
            "success": True,
            "message": "Data stored successfully in single PgVector table.",
            "doc_id": doc_id,
            "namespace": namespace,
            "chunks_count": len(chunks)
        }
            
    except Exception as error:
        session.rollback()
        print(f"Error storing data in single PgVector table: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()

async def get_vectors_and_text_single_table(request):
    """Query vectors from single table with namespace isolation"""
    try:
        body = await request.json()
        org_id = request.state.profile.get("org", {}).get("id", "")
        user = request.state.profile.get("user", {})
        embed = request.state.embed
        user_id = user['id'] if embed else None
        doc_id = body.get('doc_id')
        query = body.get('query')
        top_k = body.get('top_k', 2)
        
        if query is None and doc_id is None:
            raise HTTPException(status_code=400, detail="Query and Doc_id required.")
        
        # Create namespace for org isolation
        namespace = create_namespace(org_id)
        
        text = await get_text_from_single_table({
            'Document_id': doc_id, 
            'query': query, 
            'namespace': namespace,
            'org_id': org_id,
            'user_id': user_id,
            'top_k': top_k
        })
        
        # Check if the operation was successful based on status
        success = text.get('status') == 1
        status_code = 200 if success else 400
        
        return JSONResponse(status_code=status_code, content={
            "success": success,
            "text": text['response'],
            "namespace": namespace
        })
        
    except Exception as error:
        print(f"Error in get_vectors_and_text_single_table: {error}")
        raise HTTPException(status_code=400, detail=str(error))

async def get_text_from_single_table(args):
    """Get text from single table using namespace-based similarity search"""
    session = Session()
    try:
        doc_id = args.get('Document_id')
        query = args.get('query')
        namespace = args.get('namespace')
        org_id = args.get('org_id')
        user_id = args.get('user_id')
        top_k = args.get('top_k', 3)
        
        if query is None:
            raise HTTPException(status_code=400, detail="Query is required.")
        
        # Check if document exists in user's namespace
        doc_exists = session.query(RagVectorStore).filter_by(
            namespace=namespace,
            doc_id=doc_id
        ).first()
        
        if not doc_exists: 
            raise Exception("Invalid document id provided or document not accessible.")
        
        # Generate query embedding
        embedding = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY, model="text-embedding-3-small").embed_documents([query])
        query_embedding = embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding))
        
        # Additional query filters for CSV
        additional_filters = ""
        if doc_exists.doc_type == 'csv': 
            # Note: You can implement CSV-specific filtering here
            pass
        
        # Perform similarity search using namespace isolation (like Pinecone)
        similarity_query = text(f"""
            SELECT chunk_id, chunk_data, doc_name, chunk_index, embedding <-> :query_embedding as distance
            FROM rag_vector_store 
            WHERE namespace = :namespace 
            AND doc_id = :doc_id {additional_filters}
            ORDER BY embedding <-> :query_embedding
            LIMIT :top_k
        """)
        
        results = session.execute(similarity_query, {
            'query_embedding': str(query_embedding),
            'namespace': namespace,
            'doc_id': doc_id,
            'top_k': top_k
        }).fetchall()
        
        # Combine text from results (ordered by similarity)
        combined_text = ""
        for result in results:
            combined_text += result.chunk_data + " "
        
        return {
            'response': combined_text.strip(),
            'metadata': {
                'flowHitId': '',
                'namespace': namespace,
                'chunks_found': len(results)
            },
            'status': 1
        }
        
    except Exception as error:
        print(f"Error in get_text_from_single_table: {error}")
        return {
            'response': str(error),
            'metadata': {
                'flowHitId': '',
                'namespace': namespace if 'namespace' in locals() else ''
            },
            'status': 0
        }
    finally:
        session.close()

async def get_all_docs_single_table(request):
    """Get all documents from single table with namespace isolation"""
    session = Session()
    try:
        org_id = request.state.profile.get("org", {}).get("id", "")
        user = request.state.profile.get("user", {})
        embed = request.state.embed
        user_id = user['id'] if embed else None
        
        # Create namespace for org isolation
        namespace = create_namespace(org_id)
        
        # Get unique documents in user's namespace
        documents = session.query(RagVectorStore).filter_by(namespace=namespace).distinct(RagVectorStore.doc_id).all()
        
        # Group by doc_id to get document metadata
        doc_map = {}
        for doc in documents:
            if doc.doc_id not in doc_map:
                doc_map[doc.doc_id] = {
                    'doc_id': doc.doc_id,
                    'name': doc.doc_name,
                    'description': doc.doc_description,
                    'type': doc.doc_type,
                    'namespace': doc.namespace,
                    'created_at': doc.created_at.isoformat() if doc.created_at else None,
                    'chunks_count': 0
                }
            doc_map[doc.doc_id]['chunks_count'] += 1
        
        result = list(doc_map.values())
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": result,
            "namespace": namespace,
            "total_documents": len(result)
        })

    except Exception as error:
        print(f"Error in get_all_docs_single_table: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()

async def delete_doc_single_table(request):
    """Delete document and its chunks from single table with namespace isolation"""
    session = Session()
    try:
        body = await request.json()
        org_id = request.state.profile.get("org", {}).get("id", "")
        user = request.state.profile.get("user", {})
        embed = request.state.embed
        user_id = user['id'] if embed else None
        doc_id = body.get('doc_id')
        
        if not doc_id:
            raise HTTPException(status_code=400, detail="doc_id is required.")
        
        # Create namespace for org isolation
        namespace = create_namespace(org_id)
        
        # Find and delete all chunks for this document in user's namespace
        chunks = session.query(RagVectorStore).filter_by(
            namespace=namespace,
            doc_id=doc_id
        ).all()
        
        if not chunks:
            raise HTTPException(status_code=404, detail="Document not found in your namespace.")
        
        # Get document info before deletion
        doc_info = {
            'doc_id': chunks[0].doc_id,
            'name': chunks[0].doc_name,
            'namespace': chunks[0].namespace,
            'chunks_deleted': len(chunks)
        }
        
        # Delete all chunks for this document
        session.query(RagVectorStore).filter_by(
            namespace=namespace,
            doc_id=doc_id
        ).delete()
        
        session.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": f"Deleted document and {len(chunks)} chunks from namespace {namespace}.",
            "data": doc_info
        })
        
    except Exception as error:
        session.rollback()
        print(f"Error in delete_doc_single_table: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()

# PgVector Implementation Functions (Two-table approach - keeping for reference)

async def create_vectors_pgvector(request):
    """Create vectors and store in PgVector database"""
    try:
        # Extract the document data
        body = await request.form()
        file = body.get('file')
        file_extension = 'url'
        if file:
            file_extension = file.filename.split('.')[-1].lower()
            
            # Extract text based on file type
            if file_extension == 'pdf':
                text = await extract_pdf_text(file)
            elif file_extension == 'csv':
                text = await extract_csv_text(file)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Only PDF and CSV are supported.")
        
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
                "name": name, 
                "description": description,
                'type': file_extension,
                **(await store_in_pgvector_and_postgres(embeddings, chunks, org_id, user['id'] if embed else None, name, description, doc_id, file_extension))
            }
        )

    except HTTPException as http_error:
        print(f"HTTP error in create_vectors_pgvector: {http_error.detail}")
        raise http_error
    except Exception as error:
        traceback.print_exc()
        print(f"Error in create_vectors_pgvector: {error}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

async def store_in_pgvector_and_postgres(embeddings, chunks, org_id, user_id, name, description, doc_id, file_extension):
    """Store embeddings and chunks in PostgreSQL with PgVector"""
    session = Session()
    try:
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        # Create document record
        rag_document = RagDocument(
            name=name,
            description=description,
            doc_id=doc_id,
            org_id=org_id,
            user_id=user_id,
            type=file_extension
        )
        session.add(rag_document)
        session.flush()  # Get the ID without committing
        
        chunks_array = []
        
        # Store chunks with embeddings
        for embedding, chunk in zip(embeddings, chunks):
            chunk_id = str(uuid.uuid4())
            
            # Prepare embedding vector
            embedding_vector = embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding))
            
            rag_chunk = RagChunk(
                chunk_id=chunk_id,
                chunk_data=chunk,
                doc_id=doc_id,
                org_id=org_id,
                embedding=embedding_vector
            )
            session.add(rag_chunk)
            chunks_array.append(chunk_id)
        
        session.commit()
        
        return {
            "success": True,
            "message": "Data stored successfully in PgVector.",
            "doc_id": doc_id,
            "_id": str(rag_document.id)
        }
            
    except Exception as error:
        session.rollback()
        print(f"Error storing data in PgVector: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()

async def get_vectors_and_text_pgvector(request):
    """Query vectors and get text from PgVector database"""
    try:
        body = await request.json()
        org_id = request.state.profile.get("org", {}).get("id", "")
        doc_id = body.get('doc_id')
        query = body.get('query')
        top_k = body.get('top_k', 2)
        
        if query is None and doc_id is None:
            raise HTTPException(status_code=400, detail="Query and Doc_id required.")
        
        text = await get_text_from_vectors_query_pgvector({
            'Document_id': doc_id, 
            'query': query, 
            'org_id': org_id,
            'top_k': top_k
        })
        
        # Check if the operation was successful based on status
        success = text.get('status') == 1
        status_code = 200 if success else 400
        
        return JSONResponse(status_code=status_code, content={
            "success": success,
            "text": text['response']
        })
        
    except Exception as error:
        print(f"Error in get_vectors_and_text_pgvector: {error}")
        raise HTTPException(status_code=400, detail=str(error))

async def get_text_from_vectors_query_pgvector(args):
    """Get text from vectors using PgVector similarity search"""
    session = Session()
    try:
        doc_id = args.get('Document_id')
        query = args.get('query')
        org_id = args.get('org_id')
        top_k = args.get('top_k', 3)
        
        if query is None:
            raise HTTPException(status_code=400, detail="Query is required.")
        
        # Check if document exists
        doc_data = session.query(RagDocument).filter_by(doc_id=doc_id, org_id=org_id).first()
        
        if not doc_data: 
            raise Exception("Invalid document id provided.")
        
        # Generate query embedding
        embedding = OpenAIEmbeddings(api_key=Config.OPENAI_API_KEY, model="text-embedding-3-small").embed_documents([query])
        query_embedding = embedding[0] if isinstance(embedding, list) and len(embedding) == 1 else list(map(float, embedding))
        
        # Additional query filters for CSV
        additional_filters = ""
        if doc_data.type == 'csv': 
            # Note: You'll need to implement get_csv_query_type for PgVector or adapt it
            # to_search_for = await get_csv_query_type(doc_data, query)
            # additional_filters = f"AND chunk_type = '{to_search_for}'"
            pass
        
        # Perform similarity search using PgVector
        similarity_query = text(f"""
            SELECT chunk_id, chunk_data, embedding <-> :query_embedding as distance
            FROM rag_chunks 
            WHERE doc_id = :doc_id AND org_id = :org_id {additional_filters}
            ORDER BY embedding <-> :query_embedding
            LIMIT :top_k
        """)
        
        results = session.execute(similarity_query, {
            'query_embedding': str(query_embedding),
            'doc_id': doc_id,
            'org_id': org_id,
            'top_k': top_k
        }).fetchall()
        
        # Combine text from results
        text = ""
        for result in results:
            text += result.chunk_data + " "
        
        return {
            'response': text.strip(),
            'metadata': {
                'flowHitId': ''
            },
            'status': 1
        }
        
    except Exception as error:
        print(f"Error in get_text_from_vectors_query_pgvector: {error}")
        return {
            'response': str(error),
            'metadata': {
                'flowHitId': ''
            },
            'status': 0
        }
    finally:
        session.close()

async def get_all_docs_pgvector(request):
    """Get all documents from PgVector database"""
    session = Session()
    try:
        org_id = request.state.profile.get("org", {}).get("id", "")
        user_id = request.state.profile.get("user", {}).get('id')
        embed = request.state.embed
        
        query = session.query(RagDocument).filter_by(org_id=org_id)
        if embed:
            query = query.filter_by(user_id=user_id)
        
        documents = query.all()
        
        result = []
        for doc in documents:
            result.append({
                '_id': str(doc.id),
                'name': doc.name,
                'description': doc.description,
                'doc_id': doc.doc_id,
                'org_id': doc.org_id,
                'user_id': doc.user_id,
                'type': doc.type,
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            })
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "data": result
        })

    except Exception as error:
        print(f"Error in get_all_docs_pgvector: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()

async def delete_doc_pgvector(request):
    """Delete document and its chunks from PgVector database"""
    session = Session()
    try:
        body = await request.json()
        org_id = request.state.profile.get("org", {}).get("id", "")
        doc_id = body.get('doc_id')  # Using doc_id instead of _id for consistency
        
        if not doc_id:
            raise HTTPException(status_code=400, detail="doc_id is required.")
        
        # Find the document
        document = session.query(RagDocument).filter_by(doc_id=doc_id, org_id=org_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")
        
        # Get chunks before deletion for response
        chunks = session.query(RagChunk).filter_by(doc_id=doc_id, org_id=org_id).all()
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        # Delete chunks first (due to foreign key constraint)
        session.query(RagChunk).filter_by(doc_id=doc_id, org_id=org_id).delete()
        
        # Delete document
        session.delete(document)
        session.commit()
        
        return JSONResponse(status_code=200, content={
            "success": True,
            "message": f"Deleted document and {len(chunk_ids)} chunks from PgVector.",
            "data": {
                '_id': str(document.id),
                'name': document.name,
                'doc_id': document.doc_id,
                'deleted_chunks': chunk_ids
            }
        })
        
    except Exception as error:
        session.rollback()
        print(f"Error in delete_doc_pgvector: {error}")
        raise HTTPException(status_code=500, detail=str(error))
    finally:
        session.close()