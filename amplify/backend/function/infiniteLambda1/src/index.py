import boto3
from boto3.dynamodb.conditions import Key


def handler(event, context):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=region_name)
        input_data = json.loads(event['body'])
        roadmap = get_roadmap(input_data['roadmapId'], dynamodb)
        return {
            'statusCode': 200,
            'body': json.dumps(roadmap)
        }
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
        


def get_roadmap(roadmap_id, dynamodb):
    try:
        # Get the roadmap item
        roadmap_response = dynamodb.Table('Roadmaps').get_item(
            Key={'id': roadmap_id}
        )
        roadmap = roadmap_response.get('Item')
        if not roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")

        # Initialize the original object
        original_object = {
            'title': roadmap['title'],
            'description': roadmap['description'],
            'imageURL': roadmap['imageURL'],
            'estimatedLearningDuration': roadmap['estimatedLearningDuration'],
            'goal': roadmap['goal'],
            'currentSkillLevel': roadmap['currentSkillLevel'],
            'desiredSkillLevel': roadmap['desiredSkillLevel'],
            'currentLesson': roadmap['currentLesson'],
            'currentPhase': roadmap['currentPhase'],
            'dailyTime': roadmap['dailyTime'],
            'phases': []
        }

        # Query the phases
        phases_response = dynamodb.Table('Phases').query(
            KeyConditionExpression=Key('roadmapId').eq(roadmap_id)
        )
        phases = phases_response['Items']

        # For each phase, get the topics
        for phase in phases:
            phase_object = {
                'phaseDescription': phase['phaseDescription'],
                'topics': []
            }
            phase_id = phase['phaseId']

            topics_response = dynamodb.Table('Topics').query(
                KeyConditionExpression=Key('phaseId').eq(phase_id)
            )
            topics = topics_response['Items']

            # For each topic, get the infoBits
            for topic in topics:
                topic_object = {
                    'topicName': topic['topicName'],
                    'searchResult' : topic['searchResult'],
                    'infoBits': []
                }
                topic_id = topic['topicId']

                infobits_response = dynamodb.Table('InfoBits').query(
                    KeyConditionExpression=Key('topicId').eq(topic_id)
                )
                infobits = infobits_response['Items']

                # For each infoBit, get the quiz
                for infobit in infobits:
                    quiz_response = dynamodb.Table('Quizzes').query(
                        KeyConditionExpression=Key('infoBitId').eq(infobit['infoBitId'])
                    )
                    quiz = quiz_response['Items'][0]

                    infobit_object = {
                        'text': infobit['text'],
                        'keywords': infobit['keywords'],
                        'example': infobit.get('example', ''),
                        'quiz': {
                            'text': quiz['text'],
                            'type': quiz['type'],
                            'options': quiz.get('options', []),
                            'answer': quiz['answer']
                        }
                    }
                    topic_object['infoBits'].append(infobit_object)

                phase_object['topics'].append(topic_object)
            original_object['phases'].append(phase_object)

        return original_object

    except Exception as e:
        logger.error(f"Error: While retrieving from DB: {str(e)}")
        return None




