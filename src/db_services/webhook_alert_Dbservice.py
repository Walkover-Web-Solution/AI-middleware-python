from models.mongo_connection import db

alertModel = db['alerts']

async def get_webhook_data(org_id):
    try:
        webhook_data = list(alertModel.find({
            'org_id': org_id
        }))
        return {
            'success': True,
            'webhook_data': webhook_data or []
        }
    except Exception as error:
        print(error)
        return {
            'success': False,
            'error': error
        }

