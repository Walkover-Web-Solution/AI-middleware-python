from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from models.mongo_connection import db
from bson import ObjectId
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from config import Config


rag_parent_model = db["rag_parent_datas"]

async def create_semantic_chuncking(request,id):
    try:
        apikey =  Config.OPENAI_API_KEY
        result = await rag_parent_model.find({
            "_id": ObjectId(id)
        }).to_list(length=None)
        if apikey is None:
            raise ValueError("API key is required for semantic chunking")
        text_splitter = SemanticChunker(OpenAIEmbeddings(api_key = apikey))
        chunks = text_splitter.create_documents([result.get('content','')])
        chunk_texts = [chunk.page_content for chunk in chunks]
        return JSONResponse(status_code=200, content={
                "success": True,
                "message": "Get all functions of a org successfully",
                "chunk_texts":chunk_texts
            })
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e,)
    
