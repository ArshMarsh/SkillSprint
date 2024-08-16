from googlesearch import search
from youtubesearchpython import VideosSearch
from requests.exceptions import HTTPError

#TODO sort order and search quality
def search_resources(search_query):
    try:
        google_results = []
        for result in search(search_query, advanced=True, region="us", num_results=3):
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
