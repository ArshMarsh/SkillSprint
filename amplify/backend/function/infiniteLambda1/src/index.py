import json
import boto3
from boto3.dynamodb.conditions import Key
import logging

dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    try:
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {})
        roadmap_id = path_parameters.get('roadmapid')

        if http_method == 'GET':
            if roadmap_id:
                # Get a single roadmap by ID
                roadmap = get_roadmap(roadmap_id, dynamodb)
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
            else:
                # Get all roadmap IDs
                roadmap_ids = get_all_roadmap_ids(dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps(roadmap_ids),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

        elif http_method == 'POST':
            # Update a roadmap if roadmap_id exists; otherwise, create a new roadmap
            roadmap_data = json.loads(event['body'])
            if roadmap_id:
                update_roadmap(roadmap_id, roadmap_data, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Roadmap updated successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }
            else:
                save_roadmap(roadmap_data, dynamodb)
                return {
                    'statusCode': 201,
                    'body': json.dumps({'message': 'Roadmap created successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }

        elif http_method == 'DELETE':
            # Delete a roadmap by ID
            if roadmap_id:
                delete_roadmap(roadmap_id, dynamodb)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Roadmap deleted successfully'}),
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    }
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'roadmapid is required'}),
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
        logging.error(f"Error handling request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'details': str(e)}),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
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




def update_roadmap(roadmap_id, updated_roadmap, dynamodb):
    try:
        # Fetch the existing roadmap
        existing_roadmap_response = dynamodb.Table('Roadmaps').get_item(
            Key={'id': roadmap_id}
        )
        existing_roadmap = existing_roadmap_response.get('Item')
        if not existing_roadmap:
            raise ValueError(f"Roadmap with ID {roadmap_id} not found.")
        
        # Update the roadmap attributes
        dynamodb.Table('Roadmaps').update_item(
            Key={'id': roadmap_id},
            UpdateExpression="SET title = :title, description = :description, imageURL = :imageURL, "
                             "estimatedLearningDuration = :estimatedLearningDuration, goal = :goal, "
                             "currentSkillLevel = :currentSkillLevel, desiredSkillLevel = :desiredSkillLevel, "
                             "currentLesson = :currentLesson, currentPhase = :currentPhase, dailyTime = :dailyTime",
            ExpressionAttributeValues={
                ':title': updated_roadmap['title'],
                ':description': updated_roadmap['description'],
                ':imageURL': updated_roadmap['imageURL'],
                ':estimatedLearningDuration': updated_roadmap['estimatedLearningDuration'],
                ':goal': updated_roadmap['goal'],
                ':currentSkillLevel': updated_roadmap['currentSkillLevel'],
                ':desiredSkillLevel': updated_roadmap['desiredSkillLevel'],
                ':currentLesson': updated_roadmap['currentLesson'],
                ':currentPhase': updated_roadmap['currentPhase'],
                ':dailyTime': updated_roadmap['dailyTime'],
            }
        )

        # Update or recreate Phases, Topics, InfoBits, and Quizzes
        for phase_index, phase in enumerate(updated_roadmap['phases']):
            phase_id = f"{roadmap_id}#PHASE#{phase_index + 1}"
            dynamodb.Table('Phases').put_item(
                Item={
                    'roadmapId': roadmap_id,
                    'phaseNumber': phase_index + 1,
                    'phaseId': phase_id,
                    'phaseDescription': phase['phaseDescription']
                }
            )

            # Update or recreate Topics
            for topic_index, topic in enumerate(phase['topics']):
                topic_id = f"{phase_id}#TOPIC#{topic_index + 1}"
                dynamodb.Table('Topics').put_item(
                    Item={
                        'phaseId': phase_id,
                        'topicNumber': topic_index + 1,
                        'topicId': topic_id,
                        'topicName': topic['topicName'],
                        'searchResult': topic['searchResult']
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

    except Exception as e:
        logging.error(f"Error while updating roadmap: {str(e)}")
        return None

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

        # Delete Roadmap
        dynamodb.Table('Roadmaps').delete_item(
            Key={'id': roadmap_id}
        )

        logging.info(f"Roadmap with ID {roadmap_id} and all related data deleted successfully.")

    except Exception as e:
        logging.error(f"Error while deleting roadmap: {str(e)}")
        return None

def get_all_roadmap_ids(dynamodb):
    try:
        # Scan the Roadmaps table to get all items
        response = dynamodb.Table('Roadmaps').scan(
            ProjectionExpression='id'
        )

        roadmap_ids = [item['id'] for item in response['Items']]

        logging.info(f"Fetched {len(roadmap_ids)} roadmap IDs.")
        return roadmap_ids

    except Exception as e:
        logging.error(f"Error while retrieving roadmap IDs: {str(e)}")
        return None
