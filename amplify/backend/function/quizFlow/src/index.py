import boto3
import json
import logging
import re
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)



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
title: The title of the learning roadmap taken from INPUT (Dont includes "learning path" in "Roadmap" in this title)
description:  A detailed description explaining the content covered in phases of this roadmap and what the user will learn by following it. Limited to three sentences.
imageURL: A URL linking to an image online that can be used as the cover for this learning roadmap.
phases: Array of objects. Each object represents a phase in the learning roadmap. Atleast 4.
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. Atleast 3.
topicName:  The name of the topic.
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
Only return a valid JSON. use double quotes.
<IMPORTANT/>
    """
    
PROMPT_INFOBIT= """
    <TASK>
You are an education expert assigned to develop a personalized learning path aimed at helping users acquire specific skills.
Your main task involves analyzing an input tree of a learning path. 
Based on this analysis, you are to create "infobits" for each topic outlined in the tree. 
Infobits are concise pieces of information designed to be easily digestible by users. 
You are required to generate 4-5 infobits for each topicOutline. 
Each infobit should include a short text explaining the topic outline, 
along with relevant keywords extracted from this text. Additionally, 
optionally add an example in each infobit wherever an example would help explaining the infobit.
<TASK/>

<INPUT>
title: The title of the learning roadmap. (Dont includes "learning path" in "Roadmap" in this title)
description:  A detailed description explaining the content covered in the roadmap
goal (string): The objective the user hopes to achieve after completing the learning roadmap.
currentSkillLevel (string): The user's initial proficiency in the skill.
desiredSkillLevel (string): The proficiency level the user aims to reach.
phases: Array of objects. Each object represents a phase in the learning roadmap.
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. 
topicName:  The name of the topic.
topicOutline: Array of strings. Detailed points covering what the topic includes.
<INPUT/>

<OUTPUT>
phases: Array of objects. Each object represents a phase in the learning roadmap. Use original input structure
phaseDescription: Describes what the phase entails.
topics: Array of objects. Each object represents a topic within the phase. Use original input structure
topicName:  The name of the topic.
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
            "text": string
            "keywords" :string[]
            "example": Optional(string)
],}]}]}
<JSON_Structure/>
<OUTPUT/>
<IMPORTANT>
Only return a valid JSON, with proper delimitors and characters. use double quotes.
<IMPORTANT/>
"""


PROMPT_QUIZ = """
    <TASK>
    You are an educational content generator.
    you are given a single phase withing the roadmap.
    Based on the learning roadmap, infobit content, skill name, goal, and skill levels,
    create a quiz for each infobit within each topic in each phase.
    The quizzes should test the knowledge and understanding of the content covered.
    Use your expertise to craft quizzes that are relevant to the content and context provided.
    The quizzes should be complex depending on the phase, current skill level of user, desired skill level of user,
    and learning duration.
    The quizzes can use variations of the words from the topic and infobits.
    The quizzes can also deviate from the keywords and description if they stay relevant to the topic and infobit.
    Use various quiz types such as multiple-choice and true or false.
    Make rich and comprehensive quizzes that are engaging.
    <TASK/>

    <INPUT>
    skillName: The name of the skill the user wants to learn.
    goal: The objective the user hopes to achieve after completing the learning roadmap.
    currentSkillLevel: The user's initial proficiency in the skill.
    desiredSkillLevel: The proficiency level the user aims to reach.
    estimatedLearningDuration: The expected time to complete the learning path.
    phaseDescription: Describes what the phase entails.
    topics: Array of objects. Each object represents a topic within the phase. 
    topicName:  The name of the topic.
    infoBits: Array of objects. Each object represents an infobit for the topic.
    text: A string containing information or an explanation about the topic.
    keywords: Array of strings, comprising keywords extracted from the text.
    example: Optional string, providing an example to better explain the content in the text.
    <INPUT/>

    <OUTPUT>
    topics: Array of objects. Each object represents a topic within the phase. Use original input structure.<IMPORTANT>follow the original order of topics.<IMPORTANT/>
    topicName: The name of the topic. <IMPORTANT>follow the original name of topics.<IMPORTANT/>
    quizzes: Array of quizzes for each infobit within each topic. 
    text: The text of the quiz for that quiz for the infobit, within that topic.<IMPORTANT>follow the original order of infobits in the topic for quiz generation. the first quiz should correspond to the first infobit and so on<IMPORTANT/>
    type: The type of the quiz (e.g., multiple-choice, true-false)
    options: Array of strings (for multiple-choice quizzes). Use various multiple choice testing methodoligies such as:Ambiguous, Similar, Subtle Differences, Conceptual, Trick, Contextual, Advanced, Detailed, Counterintuitive, and Mixed Format options.
    answer: The correct answer.

    <JSON_Structure>
     {
        "topics": [
        {
            "topicName": "string",
            "quizzes": [
            {
                "text": "string",
                "type": "string",
                "options": ["string"],
                "answer": "string"
            } 
            ]
        }
        ]
    }

    <JSON_Structure/>
    <OUTPUT/>

    <IMPORTANT>
    Only return a valid JSON, with proper delimitors and characters. Use proper ',' delimiters when making multiple objects within an array. use double quotes
    <IMPORTANT/>
    """




PROMPT_QUIZ_LAST = """
    <TASK>
    You are an educational content generator.
    Based on the learning roadmap,  skill name, goal, and skill levels,infobit content, and previouses quizzes,
    create a final conclusion quiz. this is the last quiz the user will take for reaching the desired level for that skill.
    Use your expertise to craft a quiz that is relevant to the content and context provided. don't repeat the same questions in the previous quizes.
    Make rich and comprehensive quizzes that are engaging.
    if a roadmap has 1,2,3,and etc phases, this quiz should have a minimum of 1,2,3, and etc questions.
    This last final conclusion quiz should have minimum the same number of questions as there are phases in the input roadmap.
    
    <TASK/>
    <INPUT>
    title: The title of the learning roadmap. A concise name that reflects the overarching theme or skill focus of the roadmap.
    description: A detailed overview of what the roadmap covers and what users will gain from following it. Include the scope, key topics, and progression details.
    imageURL: A URL link to an image that represents or complements the learning roadmap visually.
    estimatedLearningDuration: The anticipated amount of time needed to complete the entire learning roadmap, usually expressed in months or weeks.
    goal: The end objective or skill that users will achieve by the completion of the roadmap.
    currentSkillLevel: The initial proficiency or knowledge level of the user before starting the roadmap.
    desiredSkillLevel: The target proficiency or knowledge level that the user aims to achieve upon completing the roadmap.
    currentLesson: The lesson number or identifier indicating the user's current progress within the roadmap.
    currentPhase: The phase number or identifier indicating the current stage of the learning process.
    dailyTime: The suggested amount of time the user should dedicate each day to learning.
    phases: Array of objects representing different stages in the learning roadmap.
    phaseDescription: A summary of what each phase covers and how it contributes to the overall learning objectives.
    topics: Array of objects representing individual topics within each phase.
    topicName: The title or name of the topic covered in the phase.
    topicOutline: Array of strings outlining the key points and details included in the topic.
    infoBits: Array of objects providing detailed pieces of information for each topic.
    text: A brief explanation or description of a specific aspect of the topic.
    keywords: Array of strings highlighting the main concepts or terms related to the text.
    example: An optional string providing an example to clarify or illustrate the content described in the text.
    quiz: an object containing all the info for a quiz for that infobit within that topic.
    text: The actual quiz question to test the user's understanding of the topic.
    type: The type of quiz question (e.g., multiple-choice, true-false).
    options: Array of strings providing possible answers for multiple-choice questions.
    answer: The correct answer to the quiz question.
    <INPUT/>

    <OUTPUT>
    quizzes: An array of quiz objects. each quiz object contains elements of a single quiz question. 
    text: The actual quiz question to test the user's understanding of the topic.
    type: The type of quiz question (e.g., multiple-choice, true-false).
    options: Array of strings providing possible answers for multiple-choice questions.
    answer: The correct answer to the quiz question.

    <JSON_Structure>
     {
        "quizzes": [
        {
            "text": "string",
            "type": "string",
            "options": ["string"],
            "answer": "string"
        },
        ]
    }

    <JSON_Structure/>
    <OUTPUT/>

    <IMPORTANT>
    Only return a valid JSON, with proper delimitors and characters. Use proper ',' delimiters when making multiple objects within an array. use double quotes
    <IMPORTANT/>
    """

#Claude gives misformatted JSON if Response Character count goes upto 19000
region_name = 'eu-central-1'  
def handler(event, context):
    try:
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        
        dynamodb = boto3.resource('dynamodb', region_name=region_name)


        input_data = json.loads(event['body'])
        
        roadmap_skeleton = sonnect_api_call(bedrock, PROMPT_SKELETON, input_data)
        phase_count = len(roadmap_skeleton['phases'])
        logging.info(f"Roadmap Skeleton Generated Successfully with {phase_count} Phases")
        
        phases = []
        counter = 1
        
        for phase in roadmap_skeleton['phases']:
        
            input_infobit = {
                'title': roadmap_skeleton['title'],
                'description': roadmap_skeleton['description'],
                'phases': phase,
                'goal': input_data['goal'],
                'currentSkillLevel': input_data['currentSkillLevel'],
                'desiredSkillLevel': input_data['desiredSkillLevel']
            }
            
            infobit_roadmap = sonnect_api_call(bedrock, PROMPT_INFOBIT, input_infobit)
            phases.extend(infobit_roadmap['phases'])
            logging.info(f"Roadmap InfoBits Generated Successfully for Phase {counter}")
            counter += 1
        
        logging.info("Roadmap InfoBits Generated Successfully")
        
        appended_roadmap = {
            'title': roadmap_skeleton['title'],
            'description': roadmap_skeleton['description'],
            "imageURL": roadmap_skeleton['imageURL'],
            'estimatedLearningDuration':  input_data['estimatedLearningDuration'],
            'goal': input_data['goal'],
            'currentSkillLevel': input_data['currentSkillLevel'],
            'desiredSkillLevel': input_data['desiredSkillLevel'],
            'currentLesson': 1,
            'currentPhase': 1,
            'dailyTime': input_data['desiredSkillLevel'],
            'phases': phases,
        }
        
        enhanced_roadmap = enhance_roadmap(appended_roadmap)
        for phase in enhanced_roadmap['phases']:
            input_quiz = {
                'skillName': input_data['skillName'],
                'goal': input_data['goal'],
                'currentSkillLevel': input_data['currentSkillLevel'],
                'desiredSkillLevel': input_data['desiredSkillLevel'],
                'estimatedLearningDuration': input_data['estimatedLearningDuration'],
                'phaseDescription': phase['phaseDescription'],
                'topics': phase['topics'],
            }
            
            quiz_data = sonnect_api_call(bedrock, PROMPT_QUIZ, input_quiz)
            
            # Merge the quizzes with the infobits in the phase
            for topic_index, topic in enumerate(phase['topics']):
                for infobit_index, infobit in enumerate(topic['infoBits']):
                    infobit['quiz'] = quiz_data['topics'][topic_index]['quizzes'][infobit_index]
        
        logging.info("Quizzes Generated Successfully")
        
        last_quiz = sonnect_api_call(bedrock, PROMPT_QUIZ_LAST, enhanced_roadmap)
        final_phase = {
                "phaseDescription": "Final Assessment: A comprehensive test covering all topics and phases.",
                "phaseNumber": len(enhanced_roadmap['phases']) + 1,
                "topicCount": len(last_quiz['quizzes']),
                "topics": []
            }
            
        final_topic = {
            "topicName": "Final Comprehensive Quiz",
            "topicNumber": "1",
            "infobitCount": len(last_quiz['quizzes']),
            "infoBits": []
        }
        
        for quiz in last_quiz["quizzes"]:
            infobit = {
                "text": "infobit",
                "keywords": ["keyword"],
                "example": "example",
                "quiz": quiz
            }

            final_topic["infoBits"].append(infobit) 

        final_phase['topics'].append(final_topic)
        
        enhanced_roadmap['phases'].append(final_phase)
                
        logging.info("Final Roadmap Generated Successfully")
        
        save_roadmap(enhanced_roadmap, dynamodb)

        return {
            'statusCode': 200,
            'body': enhanced_roadmap
        }

    except Exception as e:
        logger.error(f"Error: While generating roadmap: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

        
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
        
def enhance_roadmap(json_input):
    try:
        # Load the input JSON into a Python dictionary if it's a string
        if isinstance(json_input, str):
            data = json.loads(json_input)
        else:
            data = json_input
        
        phase_count = len(data['phases'])
        data['phaseCount'] = phase_count
        total_topics = 0
        
        for i, phase in enumerate(data['phases'], start=1):
            phase['phaseNumber'] = i
            
            topic_count = len(phase['topics'])
            phase['topicCount'] = topic_count
            
            for j, topic in enumerate(phase['topics'], start=1):
                topic['topicNumber'] = j + total_topics
                
                infobit_count = len(topic['infoBits'])
                topic['infobitCount'] = infobit_count
            
            total_topics = total_topics + topic_count
        
        data['totalLessons'] = total_topics
        return data
        
    except Exception as ex:
        logger.error(f"Error: While adding phase counts to roadmap: {str(ex)}")
        raise

def save_roadmap(enhanced_roadmap, dynamodb):
    try:
        roadmap_id = str(uuid.uuid4())

        # Save Roadmap
        dynamodb.Table('Roadmaps').put_item(
            Item={
                'id': roadmap_id,
                'title': enhanced_roadmap['title'],
                'description': enhanced_roadmap['description'],
                'imageURL': enhanced_roadmap['imageURL'],
                'estimatedLearningDuration': enhanced_roadmap['estimatedLearningDuration'],
                'goal': enhanced_roadmap['goal'],
                'currentSkillLevel': enhanced_roadmap['currentSkillLevel'],
                'desiredSkillLevel': enhanced_roadmap['desiredSkillLevel'],
                'currentLesson': enhanced_roadmap['currentLesson'],
                'currentPhase': enhanced_roadmap['currentPhase'],
                'dailyTime': enhanced_roadmap['dailyTime'],
            }
        )

        # Save Phases
        for phase_index, phase in enumerate(enhanced_roadmap['phases']):
            phase_id = f"{roadmap_id}#PHASE#{phase_index + 1}"
            dynamodb.Table('Phases').put_item(
                Item={
                    'roadmapId': roadmap_id,
                    'phaseNumber': phase_index + 1,
                    'phaseId': phase_id,
                    'phaseDescription': phase['phaseDescription']
                }
            )

            # Save Topics
            for topic_index, topic in enumerate(phase['topics']):
                topic_id = f"{phase_id}#TOPIC#{topic_index + 1}"
                dynamodb.Table('Topics').put_item(
                    Item={
                        'phaseId': phase_id,
                        'topicNumber': topic_index + 1,
                        'topicId': topic_id,
                        'topicName': topic['topicName'],
                        'topicOutline': topic.get('topicOutline', [])
                    }
                )

                # Save InfoBits
                for infobit_index, infobit in enumerate(topic['infoBits']):
                    infobit_id = f"{topic_id}#INFOBIT#{infobit_index + 1}"
                    dynamodb.Table('InfoBits').put_item(
                        Item={
                            'topicId': topic_id,
                            'infoBitNumber': infobit_index + 1,
                            'infoBitId': infobit_id,
                            'text': infobit['text'],
                            'keywords': infobit['keywords'],
                            'example': infobit.get('example', "")
                        }
                    )

                    # Save Quiz
                    quiz = infobit['quiz']
                    dynamodb.Table('Quizzes').put_item(
                        Item={
                            'infoBitId': infobit_id,
                            'quizNumber':  infobit_index + 1,
                            'text': quiz['text'],
                            'type': quiz['type'],
                            'options': quiz.get('options', ''),
                            'answer': quiz['answer']
                        }
                    )
        logging.info("Roadmap saved to DB successfully")

    except Exception as e:
        logger.error(f"Error: While saving to DB: {str(e)}")
