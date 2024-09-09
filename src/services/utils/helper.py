import hashlib
from Crypto.Cipher import AES
import json
from config import Config
from Crypto.Util.Padding import unpad
import traceback    
from functools import reduce
import operator
import re
from src.configs.modelConfiguration import ModelsConfig as model_configuration
import jwt
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
    def update_configuration(prev_configuration, configuration):
        for key in prev_configuration:
            prev_configuration[key] = configuration.get(key, prev_configuration[key])
        for key in configuration:
            prev_configuration[key] = configuration[key]
        if "tools" in prev_configuration and len(prev_configuration["tools"]) == 0:
            del prev_configuration["tools"]
        return prev_configuration

    @staticmethod
    def replace_variables_in_prompt(prompt, variables):
        if variables and len(variables) > 0:
            for key, value in variables.items():
                # Use json.dumps() to escape special characters
                string_value = repr(value)
                # Remove quotes at the beginning and end if they exist
                string_value = string_value[1:-1] if string_value.startswith('"') and string_value.endswith('"') else string_value
                # Escape backslashes and use raw string for regex replacement
                string_value = string_value.replace("\\", "\\\\")
                # Use raw string to avoid Unicode errors in regex
                regex = re.compile(r'\{\{' + re.escape(key) + r'\}\}')
                prompt = regex.sub(string_value, prompt)
        return prompt

    

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

    def response_middleware_for_bridge(finalResponse):
        try:
            response = finalResponse['bridge']
            model_name = response['configuration']['model'].replace("-", "_").replace(".", "_")
            configuration = getattr(model_configuration,model_name,None)
            configurations = configuration()['configuration']
            db_config = response['configuration']
            config = {}
            for key in configurations.keys():
                config[key] = db_config.get(key, response['configuration'].get(key, configurations[key].get("default", '')))
            for key in ['prompt','response_format','type', 'pre_tools','fine_tune_model']:
                config[key] = db_config.get(key, response['configuration'].get(key, {"type":'default',"cred":{}} if key == 'response_format' else ''))
            response['configuration'] = config
            finalResponse['bridge'] = response
            return finalResponse
        except json.JSONDecodeError as error:
            return {"success": False, "error": str(error)}
