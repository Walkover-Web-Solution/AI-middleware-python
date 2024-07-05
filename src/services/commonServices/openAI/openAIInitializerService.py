from openai import OpenAI

class OpenAIInitializer:
    def __init__(self, apiKey):
        self.openai = OpenAI(api_key=apiKey)
        
    def getOpenAIService(self):
        return self.openai
