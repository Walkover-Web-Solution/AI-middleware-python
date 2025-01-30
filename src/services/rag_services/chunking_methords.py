from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain.text_splitter import SemanticChunker
from langchain_community.embeddings import OpenAIEmbeddings
from typing import List, Optional

async def manual_chunking(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks manually using character-based splitting
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

async def recursive_chunking(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text recursively into chunks using multiple separators
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", "!", "?", ",", " "],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

async def semantic_chunking(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into semantically meaningful chunks using embeddings
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # embeddings = OpenAIEmbeddings()
    # text_splitter = SemanticChunker(
    #     embeddings=embeddings,
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap
    # )
    # chunks = text_splitter.split_text(text)
    # return chunks

    text_splitter = SemanticChunker(OpenAIEmbeddings())
    docs = text_splitter.create_documents([state_of_the_union])


async def agentic_chunking(text: str, chunk_size: int = 1000, chunk_overlap: int = 200, 
                          min_chunk_size: Optional[int] = None) -> List[str]:
    """
    Split text using an adaptive approach that combines multiple chunking strategies
    
    Args:
        text (str): Input text to be chunked
        chunk_size (int): Maximum size of each chunk
        chunk_overlap (int): Number of characters to overlap between chunks
        min_chunk_size (int): Minimum size for each chunk
        
    Returns:
        List[str]: List of text chunks
    """
    # First try semantic chunking
    try:
        chunks = await semantic_chunking(text, chunk_size, chunk_overlap)
        if all(len(chunk) >= (min_chunk_size or chunk_size//2) for chunk in chunks):
            return chunks
    except:
        pass
    
    # Fallback to recursive chunking
    try:
        chunks = await recursive_chunking(text, chunk_size, chunk_overlap)
        if all(len(chunk) >= (min_chunk_size or chunk_size//2) for chunk in chunks):
            return chunks
    except:
        pass
        
    # Final fallback to manual chunking
    chunks = await manual_chunking(text, chunk_size, chunk_overlap)
    return chunks

# Test code
async def test_chunking_methods():
    # Sample text for testing
    test_text = """
    This is a sample text for testing various chunking methods.
    It contains multiple paragraphs and sentences to demonstrate different splitting approaches.

    The second paragraph contains some technical information about AI and machine learning.
    Neural networks are computational models inspired by biological neural networks.
    They are used in various applications like computer vision and natural language processing.

    The third paragraph discusses some random topics.
    Weather today is sunny with a chance of rain.
    Birds are chirping in the trees nearby.
    """

    print("\nTesting Manual Chunking:")
    manual_chunks = await manual_chunking(test_text, chunk_size=200, chunk_overlap=50)
    print(f"Number of chunks: {len(manual_chunks)}")
    for i, chunk in enumerate(manual_chunks):
        print(f"Chunk {i+1}: {chunk[:100]}...")

    print("\nTesting Recursive Chunking:")
    recursive_chunks = await recursive_chunking(test_text, chunk_size=200, chunk_overlap=50)
    print(f"Number of chunks: {len(recursive_chunks)}")
    for i, chunk in enumerate(recursive_chunks):
        print(f"Chunk {i+1}: {chunk[:100]}...")

    # print("\nTesting Semantic Chunking:")
    # try:
    #     semantic_chunks = await semantic_chunking(test_text, chunk_size=200, chunk_overlap=50)
    #     print(f"Number of chunks: {len(semantic_chunks)}")
    #     for i, chunk in enumerate(semantic_chunks):
    #         print(f"Chunk {i+1}: {chunk[:100]}...")
    # except Exception as e:
    #     print(f"Semantic chunking failed: {str(e)}")

    # print("\nTesting Agentic Chunking:")
    # agentic_chunks = await agentic_chunking(test_text, chunk_size=200, chunk_overlap=50)
    # print(f"Number of chunks: {len(agentic_chunks)}")
    # for i, chunk in enumerate(agentic_chunks):
    #     print(f"Chunk {i+1}: {chunk[:100]}...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chunking_methods())
