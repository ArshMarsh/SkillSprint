from googlesearch import search
from youtubesearchpython import VideosSearch
from requests.exceptions import HTTPError
from googleapiclient.discovery import build

#TODO sort order and search quality
def search_resources(search_query):
    try:
        google_results = []
        google_searchs = search(search_query, advanced=True, region="us", num_results=3)
        for result in google_searchs :
            google_results.append({
                "title": result.title,
                "url": result.url,
                "description": result.description
            })

        video_search = VideosSearch(search_query, limit=3)
        video_results = video_search.result()["result"]

        search_results = {
            "webResult" : google_results,
            "videoResult" : video_results
        }
        return search_results
    except StopIteration:
        search_query = search_query + "tutorial"
        return search_resources(search_query)
    except Exception as e: 
        raise


def process_topics(input_data):
    image_url = None
    try:
        image_url = image_search(str(input_data['title']))
    except Exception as e:
        print("error in image search")
        
    if image_url != None:
        input_data['imageURL'] = image_url

    for phase in input_data["phases"]:
        for topic in phase['topics']:
            if 'searchResult' not in topic:
                try:
                    search_term = topic['topicSearchTerm']
                    search_result = search_resources(search_term)
                    topic['searchResult'] = search_result
                except HTTPError as e:
                    if e.response.status_code == 429:  
                        return False 
                    else: 
                        raise
                except Exception as e:
                    raise
    return True  


def image_search(query):
    api_key = 'AIzaSyD_GRf-U7E8uZPIvpz7ZpdsDYIO8FxJZcg'
    search_engine_id = '367c6bc9f286f4ed7'

    # Build the service
    service = build('customsearch', 'v1', developerKey=api_key)

    # Perform the search
    res = service.cse().list(
        q=query,
        cx=search_engine_id,
        searchType='image',
        num=1  # Get only the first result
    ).execute()

    # Extract the first image URL
    if 'items' in res:
        return res['items'][0]['link']
    return None