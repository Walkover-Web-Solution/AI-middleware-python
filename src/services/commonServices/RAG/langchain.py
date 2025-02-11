from pinecone import Pinecone
from langchain.embeddings import OpenAIEmbeddings
# from ..utility.langchain import calculate_vector_size, chunk_text_with_overlap
# from .openai import get_openai_response
# from ..enums.prompt import langchainPrompt
# from langchain.community.document_loaders.web.cheerio import CheerioWebBaseLoader
# from ..config.env import env
# from ..dbservices.chunk import ChunkService
# from undici import ProxyAgent, Dispatcher
from config import Config

MAX_REQUEST_SIZE = 4 * 1024 * 1024
pc = Pinecone(api_key=Config.PINECONE_API_KEY or "")
embeddings = OpenAIEmbeddings(
    openai_api_key=Config.OPENAI_API_KEY_EMBEDDING,
    batch_size=100,
    model='text-embedding-3-small',
)

index = pc.index(Config.PINECONE_INDEX_NAME)

async def saving_vectors_in_pinecone_batches(vectors, namespace):
    try:
        current_batch = []
        current_batch_size = 0

        for vector in vectors:
            vector_size = calculate_vector_size(vector)

            if current_batch_size + vector_size > MAX_REQUEST_SIZE:
                await index.namespace(namespace).upsert(current_batch)
                current_batch = []
                current_batch_size = 0

            current_batch.append(vector)
            current_batch_size += vector_size

        if current_batch:
            await index.namespace(namespace).upsert(current_batch)
    except Exception as error:
        raise error

async def delete_resource_chunks(namespace, resource_id):
    resource_chunks = await ChunkService.get_chunks_by_resource(resource_id)
    chunk_ids = [chunk['_id'] for chunk in resource_chunks]
    if not chunk_ids:
        return
    return await index.namespace(namespace).delete_many(chunk_ids)

async def delete_vectors_from_pinecone(vector_ids_array, namespace):
    try:
        await index.namespace(namespace).delete_many(vector_ids_array)
    except Exception as error:
        print(f"vector Id is not available {vector_ids_array} for Namespace {namespace}")

async def delete_namespace_in_pinecone(namespace):
    try:
        await index.namespace(namespace).delete_all()
    except Exception as error:
        print(f"Namespace {namespace} does not exist in Pinecone")

async def save_vectors_to_pinecone(doc_id, text, namespace):
    try:
        text_chunks = chunk_text_with_overlap(text, 512, 50)
        text_embeddings = await embeddings.embed_documents(text_chunks)
        vectors = [
            {
                'id': str(int(10000000 + random.random() * 90000000)),
                'values': embedding,
                'metadata': {'doc_id': doc_id, 'text': text_chunks[index]}
            }
            for index, embedding in enumerate(text_embeddings)
        ]
        vector_ids = [vector['id'] for vector in vectors]
        await saving_vectors_in_pinecone_batches(vectors, namespace)
        return vector_ids
    except Exception as error:
        print("Error in save_vectors_to_pinecone:", error)
        raise error

async def query_langchain(prompt, agent_id):
    try:
        print(Date.now(), "Embedding query")
        query_embedding = await embeddings.embed_query(prompt)
        print(Date.now(), "Querying Pinecone")
        query_response = await index.namespace("default").query(
            top_k=4, include_metadata=True, vector=query_embedding, filter={
                'agent_id': {'$eq': agent_id}
            }
        )
        print(Date.now(), "Pinecone response received")
        vector_ids = [match['id'] for match in query_response['matches']]
        text_chunks = await asyncio.gather(*[ChunkService.get_chunk_by_id(id)['data'] for id in vector_ids])
        vector_in_text = " ".join(text_chunks)
        return vector_in_text
    except Exception as error:
        print(error)
        raise Exception("Invalid AI response")

async def vector_search(query, agent_id):
    # TODO: Remove logs
    print(Date.now(), "Embedding query")
    query_embedding = await embeddings.embed_query(query)
    print(Date.now(), "Querying Pinecone")
    query_response = await index.namespace("default").query(
        top_k=4, include_metadata=True, vector=query_embedding, filter={
            'agent_id': {'$eq': agent_id}
        }
    )
    vector_ids = [match['id'] for match in query_response['matches']]
    print(Date.now(), "Pinecone response received")
    return vector_ids

async def get_vector_ids_from_search_text(search_text, namespace):
    query_embedding = await embeddings.embed_query(search_text)
    query_response = await index.namespace("default").query(
        top_k=5, include_metadata=True, vector=query_embedding
    )
    return query_response

async def get_crawled_data_from_site(url):
    try:
        doc_id = re.search(r'/d/(.*?)/', url).group(1)
        loader = CheerioWebBaseLoader(f"https://docs.google.com/document/d/{doc_id}/export?format=txt")
        docs = await loader.load()
        return docs[0].page_content
    except Exception as error:
        print('Error fetching the webpage:', error)
        raise error
