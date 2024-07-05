# from datetime import datetime
# from bson import ObjectId
# # from models.connection import db
# # from ...models.connection import db
# from pymongo import MongoClient
# # from config import Config
# client = MongoClient("mongodb+srv://Arpitsagarjain:Walkover123@cluster0.eo2iuez.mongodb.net/?retryWrites=true&w=majority")
# db = client["AI_Middleware"]

# print('db here', db)

# # Define the actionType schema as a dictionary
# actionTypeModel = {
#     'description': str,
#     'type': str,
#     'variable': str
# }

# # Define the configuration schema as a dictionary
# configuration_schema = {
#     'org_id': {
#         'type': str,
#         'required': True
#     },
#     'service': {
#         'type': str,
#         'default': ""
#     },
#     'bridgeType': {
#         'type': str,
#         'enum': ['api', 'chatbot'],
#         'required': True,
#         'default': 'chatbot'
#     },
#     'name': {
#         'type': str,
#         'default': ""
#     },
#     'configuration': {
#         'type': dict,
#         'default': {}
#     },
#     'apikey': {
#         'type': str,
#         'default': ""
#     },
#     'created_at': {
#         'type': datetime,
#         'default': datetime.now
#     },
#     'api_call': {
#         'type': dict,
#         'default': {}
#     },
#     'api_endpoints': {
#         'type': list,
#         'default': []
#     },
#     'is_api_call': {
#         'type': bool,
#         'default': False
#     },
#     'slugName': {
#         'type': str,
#         'required': True
#     },
#     'responseIds': {
#         'type': list,
#         'default': []
#     },
#     'responseRef': {
#         'type': ObjectId,
#         'ref': 'ResponseType'
#     },
#     'defaultQuestions': {
#         'type': list
#     },
#     'actions': {
#         'type': dict,
#         'of': actionTypeModel
#     }
# }

# # Insert index for unique constraint
# db.configuration.create_index([('org_id', 1), ('slugName', 1)], unique=True)

# # Example of inserting a new document
# new_config = {
#     'org_id': '125345',
#     'service': 'example_service',
#     'bridgeType': 'chatbot',
#     'name': 'Example Namfe',
#     'configuration': {},
#     'apikey': 'api_key_example',
#     'created_at': datetime.now(),
#     'api_call': {},
#     'api_endpoints': [],
#     'is_api_call': False,
#     'slugName': 'exampggle_slug',
#     'responseIds': [],
#     'responseRef': ObjectId(),
#     'defaultQuestions': [],
#     'actions': {
#         'example_action': {
#             'description': 'Example action description',
#             'type': 'example_type',
#             'variable': 'example_variable'
#         }
#     }
# }



# def create():
#     try:
#         db["configuration"].insert_one(new_config)
#         # print("configuration" in db["configuration"],"hhhheeeeerue")
#     except Exception as error:
#         print("hhhhhhhhhhh",error)
# create()