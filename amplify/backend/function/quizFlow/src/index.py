import json
import boto3

bedrock_client = boto3.client(service_name="bedrock-runtime", region_name="eu-central-1")


def call_llm(prompt):
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text":"say hello in the most lengthy way(10 words)"
                            }
                        ],
                    }
                ],
            }
        ),
    )
    response_body = response["body"].read()
    response_text = json.loads(response_body.decode("utf-8"))
    return response_text

def handler(event, context):
  print('received event:')
  print(event)
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps(call_llm("sth"))
  }