import json
import requests

def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip_address = response.json().get('ip')
        return ip_address
    except requests.RequestException as e:
        print(f"Error retrieving IP address: {e}")
        return None

def handler(event, context):
    input_data = json.loads(event['body'])
    
    iteration = int(input_data.get('iteration', 0)) + 1
    ip_num_key = f"iteration{iteration}_ip"
    
    iteration_package = {
        'iteration': iteration,
        ip_num_key: get_public_ip()
    }
    
    # Check if iteration count is less than or equal to 5
    if iteration < 5:
        # Recursively invoke the Lambda function
        response = context.client.invoke(
            FunctionName=context.function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps({'body': json.dumps(iteration_package)})
        )
        
        # Get the response from the recursive call
        result = json.loads(response['Payload'].read().decode('utf-8'))
        iteration_package.update(result)
    
    return {
        'statusCode': 200,
        'body': json.dumps(iteration_package)
    }
