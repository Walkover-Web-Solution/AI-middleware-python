from fastapi import APIRouter, Depends, Request, HTTPException, Body
from fastapi.responses import JSONResponse
import json
from ..services.commonServices.baseService.utils import sendResponse
import asyncio
from models.mongo_connection import db
from ..controllers.conversationController import savehistory
from ..db_services.metrics_service import updateOrCreateLastOptionData
import requests
from datetime import datetime
import pytz
from bson import ObjectId


staticFlowModel = db['staticFlow']

async def staticResponse(request: Request):
    try: 
        body = await request.json()
        chatbotCase = body.get('chatbot', None)
        staticFlowId = body['configurationData'].get('staticFlowId')

        if chatbotCase and staticFlowId:
            code = staticFlowModel.find_one({'_id': ObjectId(staticFlowId)})['staticCode']

            input_data = str(body.get('user') or body['optionSelected'].get('id') or '')
            if not input_data:
                raise ValueError("Neither 'message' nor 'id' is provided in the request body.")
            
            code += f"""
data = chat_handler.main('{input_data}')
"""
            local_vars = {}
            globalData  = {"requests": requests, "datetime":datetime, "pytz":pytz}
            exec(code, globalData, local_vars)
            static_response = local_vars.get('data')

            if static_response:
                await static_response_operation(static_response, request, input_data)
                return True
            
            elif 'user' not in body:
                body.update({'user': body['optionSelected']['name'] })
            
        await updateOrCreateLastOptionData(request.state.body['thread_id'], None)
    except Exception as e:
        # Print the stack trace and error message if an exception occurs
        print(f"Error while getting static code: {e}")



async def static_response_operation(responseToSend, request, input_data):
    
    static_response = {} 
    if isinstance(responseToSend, str):
        static_response['message'] = responseToSend
    else:
        static_response = responseToSend
        
    body = request.state.body
    response_format =   body.get('configuration', {}).get('response_format')
    # first sending message to chatbot
    data_to_send = {"data": {"content": static_response['message'], "role": "assistant"}}
    body = request.state.body
    asyncio.create_task(sendResponse(
        response_format,
        data_to_send,
        True
    ))

    # then sending mui format data
    if "muiFormat" in static_response:
        data_to_send = {"data": {"content": "", "role": "assistant"}}
        data_to_send["data"]["content"] = json.dumps(static_response.get('muiFormat', {}))
        asyncio.create_task(sendResponse(
        response_format,
        data_to_send,
        True
    ))

    #  history save api error de rahi hai
    await savehistory(
            thread_id=body['thread_id'], userMessage=input_data, botMessage=static_response['message'],
            org_id=body['org_id'], bridge_id=body['bridge_id'], model_name=body['configurationData']['configuration']['model'],
            type='chat',messageBy='assistant',  userRole="user",
            tools=None,isstatic=True
    )
    await updateOrCreateLastOptionData(body['thread_id'], static_response.get('muiFormat', {}))
    


