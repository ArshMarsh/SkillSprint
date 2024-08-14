import json
from googlesearch import search
from testingUtil import test
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
    query = "python programming"
    search_results = search(query, num_results=5, advanced=True, lang="en")

    testret = {}
    for i, result in enumerate(search_results):
        testret[i] = {
            'url': result.url,
            'title': result.title,
            'description': result.description
        }

    testret['address'] = {"address" : get_public_ip()}
    testret['layertest'] = {"message" : test()}
    return {
        'statusCode': 200,
        'headers': {
        'Access-Control-Allow-Headers': '*',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(testret)
    }


