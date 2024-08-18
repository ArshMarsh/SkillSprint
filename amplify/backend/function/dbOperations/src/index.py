import json
import boto3
from boto3.dynamodb.conditions import Key
import logging
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')


logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d in %(funcName)s]'
)

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def handler(event, context):
    try:
        http_method = event['httpMethod']
        path = event.get('path', "")
        
        path_parameters = None
        roadmap_id = None
        user_id = None
        if path != '/allRoadmap':
            path_parameters = event.get('pathParameters', {})
            roadmap_id = path_parameters.get('roadmapId', "")
            user_id = path_parameters.get('userId', "")

        if http_method == 'GET':
            if path == '/allRoadmap':
                roadmaps = convert_decimals(get_all_roadmap_details(dynamodb))
                return {
                    'statusCode': 200,
                    'body': json.dumps(roadmaps),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }
            
            if roadmap_id and '/roadmap/' in path:
                roadmap = get_roadmap(roadmap_id, dynamodb)
                roadmap = convert_decimals(roadmap)
                if roadmap:
                    return {
                        'statusCode': 200,
                        'body': json.dumps(roadmap),
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
                else:
                    return {
                        'statusCode': 404,
                        'body': json.dumps({'error': 'Roadmap not found'}),
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
            
            if user_id and '/allUserRoadmaps/' in path:
                user_roadmaps = convert_decimals(fetch_all_user_roadmaps(user_id, dynamodb))
                if user_roadmaps:
                    return {
                        'statusCode': 200,
                        'body': json.dumps(user_roadmaps),
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
                else:
                    return {
                        'statusCode': 200,
                        'body': '',
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
            
            if user_id and roadmap_id and '/userRoadmap/' in path:
                user_roadmap = convert_decimals(get_user_roadmap(user_id, roadmap_id, dynamodb))
                if user_roadmap:
                    return {
                        'statusCode': 200,
                        'body': json.dumps(user_roadmap),
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
                else:
                    return {
                        'statusCode': 404,
                        'body': json.dumps({'error': 'User roadmaps not found'}),
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*'
                        }
                    }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'roadmapId or userId is required'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

        if http_method == 'POST':
            roadmap_data = json.loads(event['body'])
            
            if path == '/allRoadmap':
                save_roadmap(roadmap_data, dynamodb)
                return {
                    'statusCode': 201,
                    'body': json.dumps({'message': 'Roadmap created successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

            if roadmap_id and '/roadmap/' in path:
                update_roadmap(roadmap_id, roadmap_data, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Roadmap updated successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

            if user_id and roadmap_id and '/userRoadmap/' in path:

                update_user_roadmap(user_id, roadmap_id, roadmap_data, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'User roadmap updated successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

        elif http_method == 'DELETE':
            if roadmap_id and '/roadmap/' in path:
                delete_roadmap(roadmap_id, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Roadmap deleted successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }
            
            if user_id and roadmap_id and '/userRoadmap/' in path:
                delete_user_roadmap(user_id, roadmap_id, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'User roadmap deleted successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': f'Method {http_method} not allowed'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

    
   
        


def get_roadmap(roadmap_id, dynamodb):
    try:
        roadmap_response = dynamodb.Table('Roadmaps').get_item(
            Key={'id': roadmap_id}
        )
        roadmap = roadmap_response.get('Item')
        if not roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")
        original_object = {
            'id' : roadmap_id,
            'title': roadmap['title'],
            'description': roadmap['description'],
            'imageURL': roadmap['imageURL'],
            'estimatedLearningDuration': roadmap['estimatedLearningDuration'],
            'goal': roadmap['goal'],
            'currentSkillLevel': roadmap['currentSkillLevel'],
            'desiredSkillLevel': roadmap['desiredSkillLevel'],
            'dailyTime': roadmap['dailyTime'],
            'phaseCount': roadmap['phaseCount'],
            'totalLessons': roadmap['totalLessons'],
            'phases': []
        }

        phases_response = dynamodb.Table('Phases').query(
            KeyConditionExpression=Key('roadmapId').eq(roadmap_id)
        )
        phases = phases_response['Items']

        for phase in phases:
            phase_object = {
                'phaseDescription': phase['phaseDescription'],
                'topicCount' : phase['topicCount'],
                'phaseNumber' : phase['phaseNumber'],
                'topics': []
            }
            phase_id = phase['phaseId']

            topics_response = dynamodb.Table('Topics').query(
                KeyConditionExpression=Key('phaseId').eq(phase_id)
            )
            topics = topics_response['Items']

            for topic in topics:
                topic_object = {
                    'topicName': topic['topicName'],
                    'searchResult' : topic['searchResult'],
                    'topicNumber' : topic['topicNumber'],
                    'infobitCount': topic['infobitCount'],
                    'infoBits': []
                }
                topic_id = topic['topicId']

                infobits_response = dynamodb.Table('InfoBits').query(
                    KeyConditionExpression=Key('topicId').eq(topic_id)
                )
                infobits = infobits_response['Items']

                for infobit in infobits:
                    quiz_response = dynamodb.Table('Quizzes').query(
                        KeyConditionExpression=Key('infoBitId').eq(infobit['infoBitId'])
                    )
                    quiz = quiz_response['Items'][0]

                    infobit_object = {
                        'infoBitId': infobit['infoBitId'],
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
        raise

def get_user_roadmap(user_id, roadmap_id, dynamodb):
    try:
        roadmap = get_roadmap(roadmap_id, dynamodb)
        if not roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")
        
        user_roadmap_response = dynamodb.Table('UserRoadmaps').get_item(
            Key={'userId': user_id, 'roadmapId': roadmap_id}
        )
        user_roadmap = user_roadmap_response.get('Item')
        if not user_roadmap:
            raise ValueError(f"User roadmap not found for user {user_id} and roadmap {roadmap_id}.")
        
        roadmap['status'] = user_roadmap['status']
        roadmap['currentLesson'] = user_roadmap['currentLesson']
        roadmap['currentPhase'] = user_roadmap['currentPhase']
        for phase in roadmap['phases']:
            for topic in phase['topics']:
                for infobit in topic['infoBits']:
                    infobit_id = infobit['infoBitId']
                    user_answer = user_roadmap['quizAnswers'].get(infobit_id, '')
                    infobit['userAnswer'] = user_answer
        
        logging.info(f"Complete roadmap for user {user_id} and roadmap {roadmap_id} fetched successfully.")
        return roadmap

    except Exception as e:
        logging.error(f"Error fetching complete user roadmap: {str(e)}")
        raise


def update_roadmap(roadmap_id, updated_roadmap, dynamodb):
    try:
        existing_roadmap_response = dynamodb.Table('Roadmaps').get_item(
            Key={'id': roadmap_id}
        )
        existing_roadmap = existing_roadmap_response.get('Item')
        if not existing_roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")
        updated_roadmap = convert_decimals(updated_roadmap)
        response = dynamodb.Table('Roadmaps').update_item(
            Key={'id': roadmap_id},
            UpdateExpression="SET title = :title, description = :description, imageURL = :imageURL, "
                             "estimatedLearningDuration = :estimatedLearningDuration, goal = :goal, "
                             "currentSkillLevel = :currentSkillLevel, desiredSkillLevel = :desiredSkillLevel, "
                             ", dailyTime = :dailyTime, phaseCount = :phaseCount, totalLessons = :totalLessons",
            ExpressionAttributeValues={
                ':title': updated_roadmap['title'],
                ':description': updated_roadmap['description'],
                ':imageURL': updated_roadmap['imageURL'],
                ':estimatedLearningDuration': updated_roadmap['estimatedLearningDuration'],
                ':goal': updated_roadmap['goal'],
                ':currentSkillLevel': updated_roadmap['currentSkillLevel'],
                ':desiredSkillLevel': updated_roadmap['desiredSkillLevel'],
                ':dailyTime': updated_roadmap['dailyTime'],
                ':phaseCount': updated_roadmap['phaseCount'],
                ':totalLessons': updated_roadmap['totalLessons']
            },
            ReturnValues="UPDATED_NEW"
        )

        # Update or recreate Phases, Topics, InfoBits, and Quizzes
        for phase_index, phase in enumerate(updated_roadmap['phases']):
            phase_id = f"{roadmap_id}#PHASE#{phase_index + 1}"
            dynamodb.Table('Phases').put_item(
                Item={
                    'roadmapId': roadmap_id,
                    'phaseNumber': phase_index + 1,
                    'phaseId': phase_id,
                    'phaseDescription': phase['phaseDescription'],
                    'topicCount':phase['topicCount']
                }
            )

            # Update or recreate Topics
            for topic_index, topic in enumerate(phase['topics']):
                topic_id = f"{phase_id}#TOPIC#{topic_index + 1}"
                dynamodb.Table('Topics').put_item(
                    Item={
                        'phaseId': phase_id,
                        'topicNumber': int(topic['topicNumber']),
                        'topicId': topic_id,
                        'topicName': topic['topicName'],
                        'searchResult': topic['searchResult'],
                        'infobitCount': topic['infobitCount']
                    }
                )

                # Update or recreate InfoBits
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

                    # Update or recreate Quizzes
                    quiz = infobit['quiz']
                    dynamodb.Table('Quizzes').put_item(
                        Item={
                            'infoBitId': infobit_id,
                            'quizNumber': infobit_index + 1,
                            'text': quiz['text'],
                            'type': quiz['type'],
                            'options': quiz.get('options', ''),
                            'answer': quiz['answer']
                        }
                    )

        logging.info(f"Roadmap with ID {roadmap_id} updated successfully.")
        logging.info(f"dynamodb response= {response}")
    except Exception as e:
        raise



def update_user_roadmap(user_id, roadmap_id, user_roadmap, dynamodb):
    try:
        quiz_answers = {}
        for phase in user_roadmap['phases']:
            for topic in phase['topics']:
                for infobit in topic['infoBits']:
                    infobit_id = infobit['infoBitId']
                    user_answer = infobit.get('userAnswer', '')
                    quiz_answers[infobit_id] = user_answer
        
        response = dynamodb.Table('UserRoadmaps').update_item(
            Key={
                'userId': user_id,
                'roadmapId': roadmap_id
            },
            UpdateExpression="SET currentLesson = :currentLesson, currentPhase = :currentPhase, quizAnswers = :quizAnswers, #status = :status",
            ExpressionAttributeNames={
                '#status': 'status'  
            },
            ExpressionAttributeValues={
                ':status': user_roadmap.get('status', 'ongoing'),  
                ':quizAnswers': quiz_answers,
                ':currentLesson': user_roadmap['currentLesson'],
                ':currentPhase': user_roadmap['currentPhase']
            },
            ReturnValues="UPDATED_NEW"
        )

        logging.info(f"User roadmap for user {user_id} and roadmap {roadmap_id} updated successfully.")
        logging.info(f"DynamoDB update response: {response}")

    except Exception as e:
        logging.error(f"Error updating user roadmap for user {user_id} and roadmap {roadmap_id}: {str(e)}")
        raise


def delete_roadmap(roadmap_id, dynamodb):
    try:
        # Fetch the existing roadmap
        roadmap_response = dynamodb.Table('Roadmaps').get_item(
            Key={'id': roadmap_id}
        )
        roadmap = roadmap_response.get('Item')
        if not roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")
        
        # Delete Phases
        phases_response = dynamodb.Table('Phases').query(
            KeyConditionExpression=Key('roadmapId').eq(roadmap_id)
        )
        phases = phases_response['Items']

        for phase in phases:
            phase_id = phase['phaseId']

            # Delete Topics for each Phase
            topics_response = dynamodb.Table('Topics').query(
                KeyConditionExpression=Key('phaseId').eq(phase_id)
            )
            topics = topics_response['Items']

            for topic in topics:
                topic_id = topic['topicId']

                # Delete InfoBits for each Topic
                infobits_response = dynamodb.Table('InfoBits').query(
                    KeyConditionExpression=Key('topicId').eq(topic_id)
                )
                infobits = infobits_response['Items']

                for infobit in infobits:
                    infobit_id = infobit['infoBitId']

                    # Delete Quizzes for each InfoBit
                    dynamodb.Table('Quizzes').delete_item(
                        Key={'infoBitId': infobit_id}
                    )

                    # Delete InfoBit
                    dynamodb.Table('InfoBits').delete_item(
                        Key={'topicId': topic_id, 'infoBitId': infobit_id}
                    )

                # Delete Topic
                dynamodb.Table('Topics').delete_item(
                    Key={'phaseId': phase_id, 'topicId': topic_id}
                )

            # Delete Phase
            dynamodb.Table('Phases').delete_item(
                Key={'roadmapId': roadmap_id, 'phaseId': phase_id}
            )

        dynamodb.Table('Roadmaps').delete_item(
            Key={'id': roadmap_id}
        )

        logging.info(f"Roadmap with ID {roadmap_id} and all related data deleted successfully.")

    except Exception as e:
        logging.error(f"Error while deleting roadmap: {str(e)}")
        raise

def delete_user_roadmap(user_id, roadmap_id, dynamodb):
    try:
        dynamodb.Table('UserRoadmaps').delete_item(
            Key={
                'userId': user_id,
                'roadmapId': roadmap_id
            }
        )
        logging.info(f"User {user_id}'s relationship with roadmap {roadmap_id} deleted successfully.")

    except Exception as e:
        logging.error(f"Error while deleting user-roadmap relationship for user {user_id} and roadmap {roadmap_id}: {str(e)}")
        raise

def get_all_roadmap_details(dynamodb):
    try:
        # Scan the Roadmaps table to get all items
        response = dynamodb.Table('Roadmaps').scan(
            ProjectionExpression='id, title, description, phaseCount, imageURL, estimatedLearningDuration, goal, currentSkillLevel, desiredSkillLevel, dailyTime, totalLessons'
        )

        roadmap_details = []
        for item in response['Items']:
            roadmap_details.append({
                'id': item['id'],
                'title': item['title'],
                'description': item['description'],
                'imageURL': item['imageURL'],
                'estimatedLearningDuration': item['estimatedLearningDuration'],
                'goal': item['goal'],
                'currentSkillLevel': item['currentSkillLevel'],
                'desiredSkillLevel': item['desiredSkillLevel'],
                'dailyTime': item['dailyTime'],
                'phaseCount': item['phaseCount'],
                'totalLessons': item['totalLessons']
            })
        
        logging.info(f"Fetched {len(roadmap_details)} roadmap details.")
        return roadmap_details

    except Exception as e:
        logging.error(f"Error while retrieving roadmap details: {str(e)}")
        raise

def fetch_all_user_roadmaps(user_id, dynamodb):
    try:
        user_roadmaps_response = dynamodb.Table('UserRoadmaps').query(
            KeyConditionExpression=Key('userId').eq(user_id)
        )
        user_roadmaps = user_roadmaps_response['Items']

        roadmap_details = []

        for user_roadmap in user_roadmaps:
            roadmap_id = user_roadmap['roadmapId']

            roadmap_response = dynamodb.Table('Roadmaps').get_item(
                Key={'id': roadmap_id},
                ProjectionExpression='id, title, description, imageURL, estimatedLearningDuration, goal, currentSkillLevel, desiredSkillLevel, dailyTime, totalLessons, phaseCount'
            )
            roadmap = roadmap_response.get('Item')

            if roadmap:
                roadmap_details.append({
                    'id': roadmap['id'],
                    'title': roadmap['title'],
                    'description': roadmap['description'],
                    'imageURL': roadmap['imageURL'],
                    'estimatedLearningDuration': roadmap['estimatedLearningDuration'],
                    'goal': roadmap['goal'],
                    'currentSkillLevel': roadmap['currentSkillLevel'],
                    'desiredSkillLevel': roadmap['desiredSkillLevel'],
                    'currentLesson': user_roadmap['currentLesson'],
                    'currentPhase': user_roadmap['currentPhase'],
                    'dailyTime': roadmap['dailyTime'],
                    'totalLessons': roadmap['totalLessons'],
                    'status': user_roadmap['status'],
                    'phaseCount': roadmap['phaseCount']
                })

        logging.info(f"Fetched {len(roadmap_details)} roadmaps for user {user_id}.")
        return roadmap_details

    except Exception as e:
        logging.error(f"Error while fetching roadmaps for user {user_id}: {str(e)}")
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
                'dailyTime': enhanced_roadmap['dailyTime'],
                'phaseCount': enhanced_roadmap['phaseCount'],
                'totalLessons': enhanced_roadmap['totalLessons']
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
                    'phaseDescription': phase['phaseDescription'],
                    'topicCount': phase['topicCount']
                }
            )

            # Save Topics
            for topic_index, topic in enumerate(phase['topics']):
                topic_id = f"{phase_id}#TOPIC#{topic_index + 1}"
                dynamodb.Table('Topics').put_item(
                    Item={
                        'phaseId': phase_id,
                        'topicNumber': int(topic['topicNumber']),
                        'topicId': topic_id,
                        'topicName': topic['topicName'],
                        'searchResult': topic['searchResult'],
                        'infobitCount' : topic['infobitCount']
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
        logging.error(f"Error saving to db: {str(e)}")
        raise


def convert_decimals(obj):
    """
    Recursively convert all Decimal values in a dictionary or list to float.
    """
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj