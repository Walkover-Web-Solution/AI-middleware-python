# from mongoengine import Document, StringField, ListField, DictField, ReferenceField

# class ChatBot(Document):
#     config = DictField(default={
#         "buttonName": '',
#         "height": '100',
#         "heightUnit": '%',
#         "width": '50',
#         "widthUnit": '%',
#         "type": 'popup',
#         "themeColor": "#000000"
#     })
#     orgId = StringField()
#     title = StringField()
#     createdBy = StringField()
#     type = StringField(default="chatbot")
#     updatedBy = StringField()
#     bridge = ListField(ReferenceField('Configuration'))  # Replace 'Configuration' with your actual model name

#     meta = {'collection': 'chatbot', 'minimize': False}

# # Export the model
# ChatBotModel = ChatBot
