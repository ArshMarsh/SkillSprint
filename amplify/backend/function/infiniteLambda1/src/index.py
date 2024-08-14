import json
import logging
import requests
from webSearcher import process_topics

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def handler(event, context):
    try:
        input_data = json.loads(event['body'])
        
        all_processed = process_topics(input_data['phases'])

        lambda_response = {
            "input_data" : input_data,
            "lambdaIndex" : -1
        }
        if not all_processed:
            lambda_input = None
            if input_data.get("lambdaIndex") is None:
                lambda_input = {
                "input_data" : input_data,
                "lambdaIndex" : 1
                }
            else:
                input_data["lambdaIndex"] = input_data["lambdaIndex"] + 1
                lambda_input = input_data
                
            lambda_response = invoke_next_lambda(lambda_input)
            return lambda_response
        
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(lambda_response["input_data"])
        }
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'lastData': input_data
            })
        }

def invoke_next_lambda(roadmap_data):
    import boto3
    
    try:
        client = boto3.client('lambda')
        
        response = client.invoke(
            FunctionName='infiniteLambda' + str(roadmap_data["lambdaIndex"]), 
            InvocationType='RequestResponse',
            Payload=json.dumps({
                'body': json.dumps(roadmap_data)
            })
        )
        logger.info(f"Next Lambda payload: {response}")

    
        if 'Payload' in response:
            response_payload = json.loads(response['Payload'].read())
        else:
            response_payload = response 

        logger.info(f"Next Lambda response: {response_payload}")

        return response_payload
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }