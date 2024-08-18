from parsel import Selector
import requests, json, re
from youtubesearchpython import VideosSearch
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api._errors import TranscriptsDisabled
from youtubesearchpython import Transcript
import boto3
import logging

from book_processor import search_download_books, find_TOC

logger = logging.getLogger()
logger.setLevel(logging.INFO)
bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='eu-central-1'  # Frankfurt region
        )

def scrape_books(query):
    params = {
        "q": query,
        "tbm": "bks",
        "hl": "en"
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.87 Safari/537.36",
    }

    html = requests.get("https://www.google.com/search", params=params, headers=headers, timeout=30)
    selector = Selector(text=html.text)
    books_results = []

    # https://regex101.com/r/mapBs4/1

    for book_result in selector.css(".Yr5TG"):
        title = book_result.css(".DKV0Md::text").get()
        link = book_result.css(".bHexk a::attr(href)").get()
        displayed_link = book_result.css(".tjvcx::text").get()
        snippet = book_result.css(".cmlJmd span::text").get()
        author = book_result.css(".fl span::text").get()
        author_link = f'https://www.google.com/search{book_result.css(".N96wpd .fl::attr(href)").get()}'
        date_published = book_result.css(".fl+ span::text").get()
        preview_link = book_result.css(".R1n8Q a.yKioRe:nth-child(1)::attr(href)").get()
        more_editions_link = book_result.css(".R1n8Q a.yKioRe:nth-child(2)::attr(href)").get()

        books_results.append({
            "title": title,
            "link": link,
            "snippet": snippet,
            "author": author,
        })

    return books_results


def scrape_youtube(search_query, search_limit=1):
    """
    Scrape YouTube videos based on a search query.
    Args:
        search_query (str): The search query to find relevant YouTube videos.
    Returns:
        list: A list of dictionaries containing information about the scraped YouTube videos with transcripts.
    """
    # Initialize an empty list to store video data
    video_data = []
    processed_videos = 0

    while len(video_data) < search_limit:
        video_search = VideosSearch(search_query, limit=search_limit + processed_videos)

        # Retrieve the list of video objects from the search results
        video_list = video_search.result()["result"]

        # Process each video
        for video in video_list[processed_videos:]:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video['id'])
                transcript_text = TextFormatter().format_transcript(transcript)
            
            except TranscriptsDisabled:
                # Skip videos without transcripts
                print(f"no transcript using api. using youtubesearch for https://www.youtube.com/watch?v={video['id']}")
                try:
                    # Get the transcript data
                    transcript_data = Transcript.get(url)

                    # Check if the transcript is empty
                    if not transcript_data['segments']:
                        pass

                    # Concatenate the text from all segments into a single string
                    transcript_text = ' '.join(segment['text'] for segment in transcript_data['segments'])
                    

                except Exception as e:
                    print(f"error: {e}")
                    pass
            except Exception as e:
                print(f"error finding captions for  using youtubesearch for https://www.youtube.com/watch?v={video['id']}")
                pass

            video_info = {
                    "title": video["title"],
                    "url": f"https://www.youtube.com/watch?v={video['id']}",
                    "views": video["viewCount"]["short"],
                    "published": video["publishedTime"],
                    "duration": video["duration"],
                    "transcript": transcript_text,
                }

            video_data.append(video_info)
            # Stop if we have enough videos
            if len(video_data) >= search_limit:
                break

        # Update the number of processed videos
        processed_videos = len(video_list)

    # Convert the video data list to JSON
    json_data = json.dumps(video_data, indent=4)
    # Optionally print the JSON data or save it to a file
    return video_data

def extract_json(response):
    try:
        json_start = response.index("{")
        json_end = response.rfind("}")
        string_result = response[json_start:json_end + 1]
        result =  json.loads(string_result)
        
        return result
    except Exception as e:
        logger.error(f"Error: While parsing JSON: {str(e)}")
        
        # If there's a JSON decode error, check if it's due to a missing comma
        match = re.search(r"Expecting ',' delimiter: line (\d+) column (\d+) \(char (\d+)\)", str(e))
        if match:
            logging.info("matched error to JSON Decode Error")
            char_position = int(match.group(3))
            # Attempt to fix the JSON by inserting a comma at the specified position
            fixed_json_str = response[:char_position] + ',' + response[char_position:]
            try:
                # Try to parse the JSON again after the fix
                json_start = response.index("{")
                json_end = response.rfind("}")
                string_result = response[json_start:json_end + 1]
                result =  json.loads(string_result)
            except Exception as ex:
                # If there's still an error, return a message
                logger.error(f"Error: While parsing JSON after fix: {str(ex)}")
                logger.error(f"string_result = {str(string_result)[char_position-40:char_position+40]}")
                raise
        else:
            # logger.error(f"string_result = {str(string_result)[char_position-10:char_position+10]}")
            raise 

def sonnect_api_call(bedrock, prompt, input_data):
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300000,
            "messages": [
                {
                    "role": "user",
                    "content": f'{prompt} INPUT = {input_data}'
                }
            ],
            "temperature": 0.2,
            "top_p": 0.9,
        }
        
        # Invoke the model
        response = bedrock.invoke_model(
            body=json.dumps(request_body),
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json"
        )
        
        # Parse and return the response
        response_body = json.loads(response['body'].read())
        response_content = response_body['content'][0]['text']
        
        try:
            result = json.loads(response_content)
        except Exception as e:
            result = extract_json(response_content)
            
        return result
    
    except Exception as e:
        logger.error(f"Error: While making API call to AI: {str(e)}")
        raise 




if __name__ == "__main__":

    # print (scrape_books("greedy algorithms"))
    # topic = 'greedy algorithms'
    # video_list = scrape_youtube(topic)
    # print(video_list)
    # for video in video_list:
    #     print(video['url'])
    #     print(video['transcript'])
    #     print("==========================\n")

def lambda_handler(event, context):
    PROMPT_SKELETON = """
        <TASK>
        You are tasked with finding the best search term for a certain skill or topic. 
        Your search term should be comprehensive, concise, specific, 
        and relevant so that the results found on book search engines 
        and YouTube search engines are useful for that skill or topic.  
        The result of the search should yield the best content for learning that topic or skill.
        <TASK/>

        <INPUT>
        Topic: skill or topic name the user wants search results for.
            The user wants to learn about this topic or skill through the result of the search query.
        <INPUT/>

        <OUTPUT>
        <JSON_Structure>
        {
        "queries": [
            "query 1",
            "query 2",
            "query 3"
        ]
        }
        <JSON_Structure/>

        <OUTPUT/>
        """

    try:
        input_data = json.loads(json.dumps(event))
        topic_name = input_data['topic']
        queries_json = sonnect_api_call(bedrock, PROMPT_SKELETON, topic_name)
        queries = json.loads(queries_json)["queries"]
        print(queries)
        video_data = scrape_youtube(queries[0])
        book_data = scrape_books(queries[0])

        first_book = book_data[0]
        title = first_book.get("title")
        author = first_book.get("author")

        book_file_name = ""
        if (title and author):
            book_file_name = search_download_books(title, author)
        else:
            book_file_name = search_download_books(topic_name)
        
    except Exception as e:
        logger.error(f"Error:{str(e)}")
        # return {
        #     'statusCode': 500,
        #     'body': json.dumps({'error': str(e)})
        # }




import libgen_scraper as lg
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
import socket
import os
import time
import PyPDF2
import re

# Function to check if a URL points to a PDF
def is_pdf_url(url):
    try:
        request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        print(f"Checking if URL points to a PDF: {url}")
        with urlopen(request) as response:
            content_type = response.getheader('Content-Type')
            is_pdf = content_type == 'application/pdf'
            print(f"URL Content-Type: {content_type} - {'PDF detected' if is_pdf else 'Not a PDF'}")
            return is_pdf
    except Exception as e:
        print(f"Error checking URL {url}: {e}")
        return False

# Function to check if a file is a valid PDF
def is_valid_pdf(filepath):
    try:
        with open(filepath, 'rb') as f:
            header = f.read(4)
            is_valid = header == b'%PDF'
            print(f"File {filepath} is {'a valid PDF' if is_valid else 'not a valid PDF'}")
            return is_valid
    except Exception as e:
        print(f"Error checking PDF validity: {e}")
        return False

# Function to check if PDF is primarily text-based
def is_text_based_pdf(filepath, min_text_ratio=0.5):
    try:
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            text_pages = 0
            print(f"Checking if PDF {filepath} is text-based...")
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text and len(text.strip()) > 100:  # Check if the text is meaningful
                    text_pages += 1

            text_ratio = text_pages / total_pages
            is_text_based = text_ratio >= min_text_ratio
            print(f"Text-based page ratio: {text_ratio:.2f} - {'Text-based PDF' if is_text_based else 'Image-based PDF'}")
            return is_text_based
    except Exception as e:
        print(f"Error checking PDF text content: {e}")
        return False

# Function to download files from given URLs and save them with specified filenames.
def download_files(urls, title, author, book_index, timeout=10, retry_attempts=3):
    for mirror_index, url in enumerate(urls):
        if not is_pdf_url(url):
            print(f"Mirror {mirror_index+1} is not a PDF, skipping...")
            continue
        
        attempt = 0
        while attempt < retry_attempts:
            try:
                print(f"Attempting to download from mirror {mirror_index+1}, attempt {attempt+1}: {url}")
                request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urlopen(request, timeout=timeout) as response:
                    content_length = response.getheader('Content-Length')
                    expected_size = int(content_length) if content_length else None
                    downloaded_size = 0
                    chunk_size = 4096

                    filename = f"{book_index}_mirror_{mirror_index+1}_{author}_{title}.pdf"
                    
                    with open(filename, 'wb') as out_file:
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            out_file.write(chunk)
                            downloaded_size += len(chunk)
                            print(f"Downloaded {downloaded_size} of {expected_size} bytes", end='\r')

                    if expected_size and downloaded_size < expected_size:
                        raise ValueError("Incomplete download detected.")

                if is_valid_pdf(filename):
                    if not is_text_based_pdf(filename):
                        print("\nPDF is mostly scanned images, deleting...")
                        os.remove(filename)
                        break
                    print(f"\nFile downloaded and verified successfully to {filename}")
                    return filename
                else:
                    print("\nDownloaded file is not a valid PDF.")
                    os.remove(filename)
            except (socket.timeout, HTTPError, URLError) as e:
                print(f"\nError during download: {e}")
            except Exception as e:
                print(f"\nError downloading file {filename}: {e}")
                if os.path.exists(filename):
                    os.remove(filename)
            
            attempt += 1
            print(f"Retrying download ({attempt}/{retry_attempts})...")
            time.sleep(2)

        print(f"Failed to download from mirror {mirror_index+1}")
        
    return None  # Return None if no successful download


def search_download_books(title, author=''):
    # Search for non-fiction books with specified criteria.
    non_fiction = lg.search_non_fiction(
        title,
        search_in_fields=lg.NonFictionSearchField.TITLE,
        filter={
            lg.NonFictionColumns.AUTHORS: author,
            lg.NonFictionColumns.LANGUAGE: r'English'
        },
        limit=10, 
        libgen_mirror="http://libgen.rs", 
    )
    # Iterate through each result and download from available mirrors.
    for book_index in range(len(non_fiction.data)):
        title = non_fiction.title(book_index)
        author = non_fiction.authors(book_index)
        print(f"\nProcessing book: {title} by {author}")

        download_links = non_fiction.download_links(book_index, limit_mirrors=5)

        downloaded_file = download_files(download_links, title.replace('/', '-'), author.replace('/', '-'), book_index, timeout=30)
        if downloaded_file:
            print(f"Successfully downloaded and verified book: {title}")
            return downloaded_file  
        else:
            print(f"Failed to download {title} from all available mirrors.")
            return None



#you get 1-2max relavent chapter -->embedding summarization-->

#s3 book --> chapter keywords llm ==> dynamo db --> use 

#video resource and web resource for each infobit

#include quiz object in each phase

#conclusion quiz 


def find_TOC(pdf_path, max_pages=100, word_density_threshold=100):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Define keywords for identifying the table of contents
        toc_keywords = [
            "Table of Contents", "Contents", "TOC", "Index", 
            "List of Topics", "Chapter Overview", "Outline",
            "Summary", "Syllabus", "Overview", "Structure",
            "Detailed Contents"
        ]
        
        toc_pages = []
        found_toc = False
        toc_detected_pages = 0
        
        for i in range(min(len(pdf_reader.pages), max_pages)):
            page = pdf_reader.pages[i]
            text = page.extract_text()
            
            # Calculate word density
            word_density = len(text.split()) if text else 0
            
            # Check for TOC keywords
            if not found_toc and any(keyword in text for keyword in toc_keywords):
                toc_pages.append(i + 1)  # PDF page numbers are 1-indexed
                found_toc = True
                toc_detected_pages += 1
                continue

            # If TOC has been found, continue to check for end indicators
            if found_toc:
                # Check if page is likely part of TOC based on word density
                if word_density < word_density_threshold:
                    toc_pages.append(i + 1)
                    toc_detected_pages += 1
                else:
                    # Transition detected; if TOC pages are significant, stop
                    if toc_detected_pages > 1:
                        break
        
        return toc_pages







if __name__ == "__main__":
    title = "automata"
    author = 'United States Parachute Association'
    print(search_download_books(title))
    # pdf_path = 'Abraham Silberschatz - Database System Concepts  7th ed.pdf'
    # toc_pages = find_table_of_contents(pdf_path)

    # if toc_pages:
    #     print("Table of Contents found on page(s):", toc_pages)
    # else:
    #     print("Table of Contents not found.")
        