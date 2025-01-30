from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
# from langchain_community.embeddings import OpenAIEmbeddings
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings

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
    # embeddings = OpenAIEmbeddings(api_key = '')
    # print(embeddings)
    # text_splitter = SemanticChunker(
    #     embeddings=embeddings,
    #     overlap=chunk_overlap
    # )
    # chunks = text_splitter.split_text(text, chunk_size=chunk_size)
    # return chunks
    text_splitter = SemanticChunker(OpenAIEmbeddings(api_key = ''))
    docs = text_splitter.create_documents([text])
    # print(docs)
    # print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiii\n")
    return docs

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

    Machine learning is a subset of artificial intelligence that focuses on data and algorithms.
    Deep learning models use neural networks with multiple layers to learn hierarchical representations.
    These networks can automatically learn features from raw data through backpropagation.

    Natural language processing combines linguistics and machine learning.
    It enables computers to understand, interpret, and generate human language.
    Applications include machine translation, sentiment analysis, and question answering.

    Pizza is a beloved dish that originated in Italy and has become popular worldwide.
    It consists of a flat, round base of dough topped with tomato sauce, cheese, and various toppings.
    This versatile meal can be customized with ingredients like pepperoni, mushrooms, and olives, making it a favorite for many occasions.

    
    """

    # print("\nTesting Manual Chunking:")
    # manual_chunks = await manual_chunking(test_text, chunk_size=200, chunk_overlap=50)
    # print(f"Number of chunks: {len(manual_chunks)}")
    # for i, chunk in enumerate(manual_chunks):
    #     print(f"Chunk {i+1}: {chunk[:100]}...")

    # print("\nTesting Recursive Chunking:")
    # recursive_chunks = await recursive_chunking(test_text, chunk_size=200, chunk_overlap=50)
    # print(f"Number of chunks: {len(recursive_chunks)}")
    # for i, chunk in enumerate(recursive_chunks):
    #     print(f"Chunk {i+1}: {chunk[:100]}...")

    # print("\nTesting Semantic Chunking:")
    # try:
    #     semantic_chunks = await semantic_chunking(test_text, chunk_size=250, chunk_overlap=50)
    #     for i, chunk in enumerate(semantic_chunks):
    #         print(f"Document {i+1}:")
    #         print("-" * 40)
    #         print("Metadata: {}\n")
    #         print("Content:\n")
    #         print(chunk)  # Ensuring clean output
    #         print("\n" + "-" * 40 + "\n")
    # except Exception as e:
    #     print(f"Semantic chunking failed: {str(e)}")

    print("\nTesting Agentic Chunking:")
    agentic_chunks = await agentic_chunking(test_text, chunk_size=200, chunk_overlap=50)
    print(f"Number of chunks: {len(agentic_chunks)}")
    for i, chunk in enumerate(agentic_chunks):
        print(f"Chunk {i+1}: {chunk[:100]}...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chunking_methods())
