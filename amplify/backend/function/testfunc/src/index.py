import json
from googlesearch import search


def handler(event, context):
    query = "python programming"
    searchs = search(query, num_results=5, advanced=True, lang="en")

    testret = {}
    for i, result in enumerate(searchs):
        testret[i] = result
  
  return {
      'statusCode': 200,
      'headers': {
          'Access-Control-Allow-Headers': '*',
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
      },
      'body': json.dumps(testret)
  }