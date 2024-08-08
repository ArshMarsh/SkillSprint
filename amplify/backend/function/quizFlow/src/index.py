import boto3
import json
import logging
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define your prompts as strings
PROMPT_SKELETON = """
<TASK>
You are an education expert tasked with designing a personalized learning path to help users achieve specific skills. Based on user input, create a structured learning roadmap that progressively builds knowledge and complexity, guiding the user from their current skill level to their desired skill level and ultimately achieving their specified goal.
<TASK/>

<INPUT>
skillName (string): The name of the skill the user wants to learn.
goal (string): The objective the user hopes to achieve after completing the learning roadmap.
currentSkillLevel (string): The user's initial proficiency in the skill.
desiredSkillLevel (string): The proficiency level the user aims to reach.
estimatedLearningDuration (string): The expected time to complete the learning path.
<INPUT/>

<OUTPUT>
title: The title of the learning roadmap taken from INPUT (Dont includes "learning path" in this title)
description: A detailed description explaining the content covered in phases of this roadmap and what the user will learn by following it. Limited to three sentences.
imageURL: A URL linking to an image online that can be used as the cover for this learning roadmap.
phases: Array of objects. Each object represents a phase in the learning roadmap. Atleast 2.
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. Atleast 3.
topicName: The name of the topic.
topicOutline: Array of strings. Detailed points covering what the topic includes. Atleast 4-5 strings
<JSON_Structure>
{title: string,
description: string,
imageURL: string,
phases: [{
phaseDescription: string,
topics: [{
topicName: string,
topicOutline: [
string ],
}]}]}
<JSON_Structure/>
<OUTPUT/>

<IMPORTANT>
Only return a valid JSON 
<IMPORTANT/>
"""

PROMPT_INFOBIT = """
<TASK>
You are an education expert assigned to develop a personalized learning path aimed at helping users acquire specific skills. Your main task involves analyzing an input tree of a learning path. Based on this analysis, you are to create "infobits" for each topic outlined in the tree. Infobits are concise pieces of information designed to be easily digestible by users. You are required to generate 4-5 infobits for each topicOutline. Each infobit should include a short text explaining the topic outline, along with relevant keywords extracted from this text. Additionally, optionally add an example in each infobit wherever an example would help explaining the infobit.
<TASK/>

<INPUT>
title: The title of the learning roadmap.
description: A detailed description explaining the content covered in the roadmap
goal (string): The objective the user hopes to achieve after completing the learning roadmap.
currentSkillLevel (string): The user's initial proficiency in the skill.
desiredSkillLevel (string): The proficiency level the user aims to reach.
phases: Array of objects. Each object represents a phase in the learning roadmap.
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. 
topicName: The name of the topic.
topicOutline: Array of strings. Detailed points covering what the topic includes.
<INPUT/>

<OUTPUT>
phases: Array of objects. Each object represents a phase in the learning roadmap. Use original input structure
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. Use original input structure
topicName: The name of the topic.
infoBits: Array of objects. Each object represents an infobit for the topic.
text: A string containing information or an explanation about the topic, derived from the topic outline.
keywords: Array of strings, comprising keywords extracted from the text. Maximum 5 keywords.
example: Optional string, providing an example to better explain the content in the text.
<JSON_Structure>
phases: [{
"phaseDescription": string,
"topics": [{
"topicName": string,
"infoBits": [
"text": string,
"keywords": string[],
"example": Optional(string)
],}]}]}
<JSON_Structure/>
<OUTPUT/>
<IMPORTANT>
Only return a valid JSON, with proper delimitors and characters
<IMPORTANT/>
"""

PROMPT_QUIZ = """
<TASK>
You are an educational content generator. Based on the learning roadmap and infobit content provided, create a set of quizzes for each phase and topic. The quizzes should test the knowledge and understanding of the content covered. Use your own knowledge to make relevant quizzes to the content provided. The quizzes should be complex depending on the phase, current skill level of user, desired skill level of user, and learning duration. The quizzes can use variations of the words from the topic and keywords and deviate. Use various question types such as multiple-choice, true or false, and short-answer questions.
<TASK/>

<INPUT>
title: The title of the learning roadmap.
description: A brief description of the roadmap.
phases: Array of objects. Each object represents a phase in the roadmap with topics and infobits.
<INPUT/>

<OUTPUT>
quizzes: Array of objects. Each object represents a quiz for a specific phase.
phase: The name of the phase.
topics: Array of objects. Each object represents a topic within the phase.
topicName: The name of the topic.
questions: Array of objects. Each object represents a question.
question: The text of the question.
type: The type of the question (e.g., multiple-choice, true-false, short-answer).
options: Array of strings (for multiple-choice questions).
answer: The correct answer.
<OUTPUT/>
<IMPORTANT>
Only return a valid JSON, with proper delimitors and characters
<IMPORTANT/>
"""



def handler(event, context):
    # Create a Bedrock Runtime client
    try:
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='eu-central-1'  # Frankfurt region
        )

        input_data = json.loads(json.dumps(event))

        # Generate the initial roadmap skeleton
        roadmap_skeleton = sonnect_api_call(bedrock, PROMPT_SKELETON, input_data)
        phase_count = len(roadmap_skeleton['phases'])
        logging.info(f"Roadmap Skeleton Generated Successfully with {phase_count} Phases")

        phases = []
        counter = 1

        for phase in roadmap_skeleton['phases']:
            # Prepare input for Infobit generation
            input_infobit = {
                'title': roadmap_skeleton['title'],
                'description': roadmap_skeleton['description'],
                'phases': [phase],  # Correctly format phases
                'goal': event['goal'],
                'currentSkillLevel': input_data['currentSkillLevel'],
                'desiredSkillLevel': input_data['desiredSkillLevel']
            }
            
            infobit_roadmap = sonnect_api_call(bedrock, PROMPT_INFOBIT, input_infobit)
            phases.extend(infobit_roadmap['phases'])
            logging.info(f"Roadmap InfoBits Generated Successfully for Phase {counter}")
            counter += 1

        logging.info("Roadmap InfoBits Generated Successfully")

        # Append infobits to the roadmap
        appended_roadmap = {
            'title': roadmap_skeleton['title'],
            'description': roadmap_skeleton['description'],
            'imageURL': roadmap_skeleton['imageURL'],
            'phases': phases
        }

        final_result = appended_roadmap

        logging.info("Base Roadmap Generated Successfully")
        
        # Generate quizzes based on the roadmap and infobits
        quiz_input = {
            'title': final_result['title'],
            'description': final_result['description'],
            'phases': final_result['phases']
        }

        quizzes = sonnect_api_call(bedrock, PROMPT_QUIZ, quiz_input)
        
        # Ensure quizzes are correctly included in final results
        final_result['quizzes'] = quizzes['quizzes']

        logging.info("Quizzes Generated Successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps(final_result)
        }
    except Exception as e:
        logger.error(f"Error: while generating roadmap {str(e)}")

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
    
def extract_json(response):
    try:
        json_start = response.index("{")
        json_end = response.rfind("}")
        string_result = response[json_start:json_end + 1]
        result = json.loads(string_result)
        
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
                result = json.loads(string_result)
            except Exception as ex:
                # If there's still an error, return a message
                logger.error(f"Error: While parsing JSON after fix: {str(ex)}")
                logger.error(f"string_result = {str(string_result)[char_position-40:char_position+40]}")
                raise
        else:
            # logger.error(f"string_result = {str(string_result)[char_position-10:char_position+10]}")
            raise 

def enhance_roadmap(json_input):
    # Load the input JSON into a Python dictionary if it's a string
    if isinstance(json_input, str):
        data = json.loads(json_input)
    else:
        data = json_input
    
    phase_count = len(data['phases'])
    data['PhaseCount'] = str(phase_count)
    
    for i, phase in enumerate(data['phases'], start=1):
        if not isinstance(phase, dict):
            phase = dict(phase)
        phase['PhaseNumber'] = str(i)
        
        topics = phase.get('topics', [])
        if not isinstance(topics, list):
            topics = [dict(topics)]
        
        topic_count = len(topics)
        phase['TopicCount'] = topic_count
        
        for j, topic in enumerate(topics, start=1):
            if not isinstance(topic, dict):
                topic = dict(topic)
            topic['TopicNumber'] = str(j)
            
            info_bits = topic.get('infoBits', [])
            if not isinstance(info_bits, list):
                info_bits = [dict(info_bits)]
                
            infobit_count = len(info_bits)
            topic['InfobitCount'] = str(infobit_count)
            
        phase['topics'] = topics  
    
    return data





