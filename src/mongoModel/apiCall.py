# import mongoengine as me
# from datetime import datetime

# class ApiCall(me.Document):
#     org_id = me.StringField(default="")
#     bridge_id = me.StringField(default="")
#     activated = me.BooleanField(default=False)
#     required_fields = me.ListField(me.StringField(), default=[])
#     short_description = me.StringField(default='')
#     axios = me.StringField(default='')
#     optional_fields = me.ListField(me.StringField(), default=[])
#     endpoint = me.StringField(default="")
#     api_description = me.StringField()
#     created_at = me.DateTimeField(default=datetime.now)

#     meta = {
#         'collection': 'apicall'
#     }

# # Assuming you want to export it in a similar way to how ES6 modules work
# apiCallModel = ApiCall
