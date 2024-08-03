from ...configs.constant import service_name
from ....src.configs.models.gemini import gemini
from ....src.configs.models.openai import openai
from ....src.configs.models.grokk import grokk
from ....src.configs.models.anthropic import anthrophic
class common:
    @staticmethod
    async def get_func_name(service, modelname):
        if service_name['openai']  == service:
            return  getattr(openai, modelname, None)
        elif service_name['gemini']  == service:
            return  getattr(gemini, modelname, None)
        elif service_name['grokk']  == service:
            return  getattr(grokk, modelname, None)
        elif service_name['anthrophic']  == service:
            return  getattr(anthrophic, modelname, None)

__all__ = ["common"]