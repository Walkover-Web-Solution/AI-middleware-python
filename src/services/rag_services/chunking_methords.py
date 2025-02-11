from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from config import Config

apikey = Config.OPENAI_API_KEY
async def manual_chunking(text, chunk_size = 1000, chunk_overlap =  200):
    """
    Split text into chunks manually using character-based splitting
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    try:
        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        embeddings = []
        for chunk in chunks:
            embedding = OpenAIEmbeddings(api_key=apikey).embed_text(chunk)
            embeddings.append(embedding)
        return chunks, embeddings
    except Exception as e:
        print(f"Error during manual chunking: {str(e)}")
        raise

async def recursive_chunking(text, chunk_size = 1000, chunk_overlap = 200):
    """
    Split text recursively into chunks using multiple separators
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", ",", " "],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        embeddings = []
        for chunk in chunks:
            embedding = OpenAIEmbeddings(api_key=apikey).embed_text(chunk)
            embeddings.append(embedding)
        return chunks, embeddings
    except Exception as e:
        print(f"Error during recursive chunking: {str(e)}")
        raise

async def semantic_chunking(text):
    """
    Split text into semantically meaningful chunks using embeddings
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    try:
        if apikey is None:
            raise ValueError("API key is required for semantic chunking")
        text_splitter = SemanticChunker(OpenAIEmbeddings(api_key = apikey))
        chunks = text_splitter.create_documents([text])
        # Convert Document objects to plain text for better readability
        chunk_texts = [chunk.page_content for chunk in chunks]
        print(chunk_texts)
        embeddings = []
        for chunk in chunk_texts:
            embedding = OpenAIEmbeddings(api_key=apikey).embed_documents([chunk])
            embeddings.append(embedding)
        return chunk_texts, embeddings
    except Exception as e:
        print(f"Error during semantic chunking: {str(e)}")
        raise



