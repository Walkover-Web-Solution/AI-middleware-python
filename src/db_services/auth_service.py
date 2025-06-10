from models.mongo_connection import db

auth_model = db['auth']

async def save_auth_token_in_db(client_id, redirection_url, org_id):
    await auth_model.insert_one({
        'client_id': client_id,
        'redirection_url': redirection_url,
        'org_id': org_id
    })
    return True

async def verify_auth_token(client_id, redirection_url):
    result = await auth_model.find_one({
        'client_id': client_id,
        'redirection_url': redirection_url
    })
    return result
