import boto3
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d in %(funcName)s]'
)

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)



dynamodb = boto3.resource('dynamodb')
def handler(event, context):
    try:
        user_id = event['pathParameters']['userId']
        
        if event['httpMethod'] == 'GET':
            return get_item_from_dynamodb(user_id)
        
        elif event['httpMethod'] == 'POST':
            body = json.loads(event['body'])
            skills = body.get('skills', [])
            pdf_data = body['pdf'].encode('latin1')
            text = extract_text_from_pdf(pdf_data)
            return store_or_update_dynamodb_item(user_id, skills, text)

        else:
            return {"statusCode": 405, "body": "Method Not Allowed"}
    
    except Exception as e:
        logger.error(f"Failed to process request: {e}")
        return {"statusCode": 500, "body": "Internal Server Error: Failed to process the request."}



def get_item_from_dynamodb(user_id):
    try:
        response = table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            return {"statusCode": 200, "body": json.dumps(response['Item'])}
        else:
            return {"statusCode": 404, "body": "Item not found."}
    
    except ClientError as e:
        logger.error(f"Failed to get data from DynamoDB: {e}")
        return {"statusCode": 500, "body": "Internal Server Error: Failed to get data from DynamoDB."}


table = dynamodb.Table('UserRoadmaps')
def store_or_update_dynamodb_item(user_id, skills=None, text=None):
    try:
        existing_item = table.get_item(Key={'userId': user_id})
        
        if 'Item' in existing_item:
            update_expression = []
            expression_attribute_values = {}

            if skills:
                update_expression.append('Skills = :s')
                expression_attribute_values[':s'] = skills

            if text:
                update_expression.append('ResumeText = :r')
                expression_attribute_values[':r'] = text

            if not update_expression:
                logger.info(f"No updates required for userId {user_id}. Both fields are empty.")
                return {"statusCode": 200, "body": "No updates required. Fields are empty."}

            update_expression = 'SET ' + ', '.join(update_expression)

            table.update_item(
                Key={'userId': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            logger.info(f"Data updated successfully for userId {user_id}.")
            return {"statusCode": 200, "body": "Update successful."}
        else:
            table.put_item(
                Item={
                    'userId': user_id,
                    'Skills': skills,
                    'ResumeText': text
                }
            )
            logger.info(f"Data stored successfully for userId {user_id}.")
            return {"statusCode": 200, "body": "Data stored successfully."}
    
    except ClientError as e:
        logger.error(f"Failed to store or update data in DynamoDB: {e}")
        return {"statusCode": 500, "body": "Internal Server Error: Failed to store or update data in DynamoDB."}

def extract_text_from_pdf(pdf_data):
    try:
        reader = PdfReader(BytesIO(pdf_data))
        text = ''.join([page.extract_text() for page in reader.pages])
        if text.strip():
            return text
    except Exception as e:
        logger.error(f"Error reading PDF with PyPDF2: {e}")
    
    try:
        images = convert_from_bytes(pdf_data)
        text = ''.join([pytesseract.image_to_string(image) for image in images])
        return text
    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        return ""


