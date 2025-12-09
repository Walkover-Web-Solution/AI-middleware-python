from src.services.utils.openai_client import get_async_openai_client


async def embedding_model(configuration, apiKey):
    try:
        openAI = get_async_openai_client(api_key=apiKey)
        embedding = await openAI.embeddings.create(**configuration)
        return {'success': True, 'response': embedding.to_dict()}
            
    except Exception as error:
        print("error", error)
        return {
            'success': False,
            'error': str(error)
        }


