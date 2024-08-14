from googlesearch import search
from youtubesearchpython import VideosSearch
from requests.exceptions import HTTPError

#TODO sort order and search quality
def search_resources(search_query):
    try:
        google_results = next(search(search_query, advanced=True, region="us", num_results=2))
        google_result = {
            "title" : google_results.title,
            "url"   : google_results.url,
            "description" : google_results.description
        }
        video_search = VideosSearch(search_query, limit=2)
        video_result = video_search.result()["result"][0]

        search_results = {
            "webResult" : google_result,
            "videoResult" : video_result
        }
        return search_results
    except StopIteration:
        search_query = search_query + "tutorial"
        return search_resources(search_query)
    except Exception as e: 
        raise
    

def process_topics(phases):
    for phase in phases:
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
