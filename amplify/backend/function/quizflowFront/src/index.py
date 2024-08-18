
import boto3
import json
def handler(event, context):
    try:
        

        client = boto3.client('lambda')
            
        response = client.invoke(
            FunctionName= "quizFlow-frontend", 
            InvocationType='Event',
            Payload=json.dumps({
                'body': event['body']
            })
        )
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': 'quizflow invoked successfuly'
        }
    except Exception as e:
         return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': f'error: {str(e)}'
        }