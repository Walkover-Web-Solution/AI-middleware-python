from openai import AsyncOpenAI

class OpenAIInitializer:
    def __init__(self, apiKey):
        self.openai = AsyncOpenAI(api_key=apiKey)
        
    def getOpenAIService(self):
        return self.openai
    