import hashlib
from Crypto.Cipher import AES
import pydash as _
import json
from config import Config
from Crypto.Util.Padding import unpad
import traceback    
from functools import reduce
import operator
import re
from src.configs.model_configuration import model_config_document
import jwt
from ..commonServices.openAI.openaiCall import UnifiedOpenAICase
from ..commonServices.openAI.openai_batch import OpenaiBatch
from ..commonServices.groq.groqCall import Groq
from ..commonServices.anthrophic.antrophicCall import Antrophic
from ...configs.constant import service_name
from ..commonServices.openAI.openai_embedding_call import OpenaiEmbedding
from ..cache_service import find_in_cache, store_in_cache
from ..utils.apiservice import fetch
from datetime import datetime, timezone, timedelta
import pytz
class Helper:
    @staticmethod
    def encrypt(text):
        iv = hashlib.sha512(Config.Secret_IV.encode()).hexdigest()[:16]
        key = hashlib.sha512(Config.Encreaption_key.encode()).hexdigest()[:32]
        cipher = AES.new(key.encode(), AES.MODE_CFB, iv.encode())
        encrypted = cipher.encrypt(text.encode())
        return encrypted.hex()

    @staticmethod
    def decrypt(encrypted_text):
        token = None
        encryption_key=Config.Encreaption_key
        secret_iv=Config.Secret_IV
        
        iv = hashlib.sha512(secret_iv.encode()).hexdigest()[:16]
        key = hashlib.sha512(encryption_key.encode()).hexdigest()[:32]

        encrypted_text_bytes = bytes.fromhex(encrypted_text)
        try:
            # Attempt to decrypt using AES CBC mode
            cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
            decrypted_bytes = unpad(cipher.decrypt(encrypted_text_bytes), AES.block_size)
            token = decrypted_bytes.decode('utf-8')
        except (ValueError, KeyError) as e:
            # Attempt to decrypt using AES CFB mode
            cipher = AES.new(key.encode(), AES.MODE_CFB, iv.encode())
            decrypted_bytes = cipher.decrypt(encrypted_text_bytes)
            token = decrypted_bytes.decode('utf-8')
        return token
    
    @staticmethod 
    def mask_api_key(key):
        if not key:
            return ''
        if len(key) > 6:
            return key[:3] + '*' * (9) + key[-3:]
        return key
         

    @staticmethod
    def update_configuration(prev_configuration, configuration):
        for key in prev_configuration:
            prev_configuration[key] = configuration.get(key, prev_configuration[key])
        for key in configuration:
            prev_configuration[key] = configuration[key]
        if "tools" in prev_configuration and len(prev_configuration["tools"]) == 0:
            del prev_configuration["tools"]
        return prev_configuration

    @staticmethod
    def replace_variables_in_prompt(prompt, Aviliable_variables):
        missing_variables = {}
        placeholders = re.findall(r'\{\{(.*?)\}\}', prompt)
        flattened_json = Helper.custom_flatten(Aviliable_variables)
        variables = {**Aviliable_variables, **flattened_json}

        if variables:
            for key, value in variables.items():
                if key in placeholders:
                    string_value = str(value)
                    string_value = string_value[1:-1] if string_value.startswith('"') and string_value.endswith('"') else string_value
                    string_value = string_value.replace("\\", "\\\\")
                    regex = re.compile(r'\{\{' + re.escape(key) + r'\}\}')
                    prompt = regex.sub(string_value, prompt)
                    placeholders.remove(key)

        for placeholder in placeholders:
            missing_variables[placeholder] = f"{{{{{placeholder}}}}}"

        return prompt, missing_variables


    @staticmethod
    def custom_flatten(d, parent_key='', sep='.'):
        """
        Flattens a dictionary and preserves nested structures.
        :param d: Dictionary to flatten
        :param parent_key: The base key string
        :param sep: Separator between keys
        :return: A flattened dictionary with nested structures preserved
        """
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                # Add the current nested structure as a whole
                items[new_key] = v
                # Flatten recursively
                items.update(Helper.custom_flatten(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    @staticmethod
    def parse_json(json_string):
        try:
            return {"success": True, "json": json.loads(json_string)}
        except json.JSONDecodeError as error:
            return {"success": False, "error": str(error)}

    def get_value_from_location(obj, location):
        try:
            keys = location.split(".")
            keys = [int(key) if key.isdigit() else key for key in keys]
            
            value = reduce(operator.getitem, keys, obj)
            return value
        except Exception as e:
            traceback.print_exc()
            return None
    def generate_token(payload, accesskey):
        return jwt.encode(payload, accesskey)

    def response_middleware_for_bridge(service, finalResponse):
        try:
            response = finalResponse['bridge']
            model = response['configuration']['model']
            modelObj = model_config_document[service][model]
            configurations = modelObj['configuration']
            db_config = response['configuration']
            # if response.get('apikey'):
            #     decryptedApiKey = Helper.decrypt(response['apikey'])
            #     maskedApiKey = Helper.mask_api_key(decryptedApiKey)
            #     response['apikey'] = maskedApiKey
            config = {}
            for key in configurations.keys():
                config[key] = db_config.get(key, response['configuration'].get(key, configurations[key].get("default", '')))
            for key in ['prompt','response_format','type', 'pre_tools','fine_tune_model', 'is_rich_text','tonePrompt','responseStylePrompt']:
                if key == 'response_format':
                    config[key] = db_config.get(key, response['configuration'].get(key, {"type":'default',"cred":{}}))
                elif key == 'fine_tune_model':
                    config[key] = db_config.get(key, response['configuration'].get(key, {}))
                elif key == 'type':
                    config[key] = db_config.get(key, response['configuration'].get(key, 'chat'))
                elif key == 'pre_tools':
                    config[key] = db_config.get(key, response['configuration'].get(key, []))
                elif key == 'is_rich_text':
                    config[key] = db_config.get(key, response['configuration'].get(key, True))
                else:
                    config[key] = db_config.get(key, response['configuration'].get(key, ''))
            response['configuration'] = config
            finalResponse['bridge'] = response
            return finalResponse
        except json.JSONDecodeError as error:
            return {"success": False, "error": str(error)}
        
    def find_variables_in_string(prompt):
        variables = re.findall(r'{{(.*?)}}', prompt)
        return variables
    
    async def create_service_handler(params, service):
        if service == service_name['openai']:
            class_obj = UnifiedOpenAICase(params)
        # elif service == service_name['gemini']:
        #     class_obj = GeminiHandler(params)
        elif service == service_name['anthropic']:
            class_obj = Antrophic(params)
        elif service == service_name['groq']:
            class_obj = Groq(params)
            
        return class_obj

    
    def calculate_usage(model, model_response, service):
        usage = {}
        token_cost = {}
        permillion = 1000000
        modelObj = model_config_document[service][model]
        if modelObj is None:
            raise AttributeError(f"Model function '{model}' not found in model_configuration.")

        if service in ['openai', 'groq']:
            token_cost['input_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('input_cost') or 0
            token_cost['output_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('output_cost') or 0
            token_cost['cache_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('cached_cost') or 0
            
            usage["inputTokens"] = _.get(model_response['usage'], 'input_tokens', 0)
            usage["outputTokens"] = _.get(model_response['usage'], 'output_tokens', 0)
            usage["cachedTokens"] = _.get(model_response['usage'], 'cached_token') or 0

            usage["expectedCost"] = 0
            if usage["inputTokens"]:
                usage["expectedCost"] += usage['inputTokens'] * (token_cost['input_cost'] / permillion)
            if usage["outputTokens"]:
                usage["expectedCost"] += usage['outputTokens'] * (token_cost['output_cost'] / permillion)
            if usage["cachedTokens"]:
                usage["expectedCost"] += usage['cachedTokens'] * (token_cost['cache_cost'] / permillion)

        elif service == 'anthropic':
            # model_specific_config = model_response['usage'][0].get('total_cost', {}).get(model, {})
            usage["inputTokens"] = _.get(model_response['usage'], 'input_tokens', 0)
            usage["outputTokens"] = _.get(model_response['usage'], 'output_tokens', 0)
            usage["cachedCreationInputTokens"] = _.get(model_response['usage'], 'cache_creation_input_tokens') or 0
            usage["cachedReadInputTokens"] = _.get(model_response['usage'], 'cache_read_input_tokens') or 0

            token_cost['input_cost'] = modelObj['outputConfig']['usage'][0]['total_cost']['input_cost']
            token_cost['output_cost'] = modelObj['outputConfig']['usage'][0]['total_cost']['output_cost']
            token_cost['cached_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('cached_cost') or 0
            token_cost['caching_write_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('caching_write_cost') or 0
            token_cost['caching_read_cost'] = modelObj['outputConfig']['usage'][0]['total_cost'].get('caching_read_cost') or 0

            usage["expectedCost"] = 0
            if usage["inputTokens"]:
                usage["expectedCost"] += usage['inputTokens'] * (token_cost['input_cost'] / permillion)
                usage["expectedCost"] += usage['inputTokens'] * (token_cost['caching_read_cost'] / permillion)
                usage["expectedCost"] += usage['cachedCreationInputTokens'] * (token_cost['caching_read_cost'] / permillion) 

            if usage["outputTokens"]:
                usage["expectedCost"] += usage['outputTokens'] * (token_cost['output_cost'] / permillion)
                usage["expectedCost"] += usage['cachedReadInputTokens'] * (token_cost['caching_write_cost'] / permillion)

        return usage
    
    async def create_service_handler_for_batch(params, service):
        if service == service_name['openai']:
            class_obj = OpenaiBatch(params)
        # elif service == service_name['gemini']:
        #     class_obj = GeminiHandler(params)
        # elif service == service_name['anthropic']:
        #     class_obj = Antrophic(params)
        # elif service == service_name['groq']:
        #     class_obj = Groq(params)
            
        return class_obj

    async def embedding_service_handler(params, service):
        if service == service_name['openai']:
            class_obj = OpenaiEmbedding(params)
        return class_obj
    
    def add_doc_description_to_prompt(prompt, rag_data):
        prompt += '\n Available Knowledge Base :- Here are the available documents to get data when needed call the function get_knowledge_base_data: \n' +  '\n'.join([f"name : {data.get('name')}, description : {data.get('description')},  doc_id : {data.get('_id')} \n" for data in rag_data])    
        return prompt
        
    async def get_timezone_and_org_name(org_id):
        cached_data = await find_in_cache(org_id)
        if cached_data:
            # Deserialize the cached JSON data
            cached_result = json.loads(cached_data)
            return cached_result
        else:
            response, _ = await fetch(f"https://routes.msg91.com/api/{Config.PUBLIC_REFERENCEID}/getCompanies?id={org_id}", "GET", {"Authkey": Config.ADMIN_API_KEY}, None, None)
            await store_in_cache(org_id, response.get('data', {}).get('data', [{}])[0])
            return response.get('data', {}).get('data', [{}])[0]
    def sort_bridges(bridges, metrics_data):
        # Create a dictionary to map _id to total tokens
        token_map = {_id: tokens for _id, tokens in metrics_data}
        
        # Split bridges into those with and without metrics data
        present = []
        not_present = []
        for bridge in bridges:
            if bridge['_id'] in token_map:
                bridge['total_tokens'] = token_map[bridge['_id']]
                present.append(bridge)

            else:
                bridge['total_tokens'] = 0
                not_present.append(bridge)
        
        # Sort the present bridges by descending token count
        # present.sort(key=lambda x: token_map[x['_id']], reverse=True)
        
        # Combine the lists, keeping not_present bridges in their original order at the end
        return present + not_present
    


    def get_current_time_with_timezone(tz_identifier):
        try:
            tz = pytz.timezone(tz_identifier)
            offset = datetime.now(tz).utcoffset()
            hours, remainder = divmod(offset.total_seconds(), 3600)
            minutes = remainder // 60
            return int(hours), int(minutes)
        except Exception as e:
            return f"Invalid timezone: {e}"