from openai import AsyncOpenAI


async def embedding_model(configuration, apiKey):
    """Call OpenAI embedding endpoint and wrap the response."""
    try:
        openAI = AsyncOpenAI(api_key=apiKey)
        embedding = await openAI.embeddings.create(**configuration)
        return {'success': True, 'response': embedding.to_dict()}
            
    except Exception as error:
        print("error", error)
        return {
            'success': False,
            'error': str(error)
        }

