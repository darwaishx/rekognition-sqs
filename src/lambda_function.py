from __future__ import print_function

import boto3
from decimal import Decimal
import json
import os

def getLabels(rekognition, bucket, image, ddb, pk):
    #Label and activity detection
    labels = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': image,
            }
        },
    )

    ti = 0

    for label in labels['Labels']:
        ddbResponse = ddb.put_item(
                    Item={
                          'pk': pk,
                          'sk': '1-label-' + str(ti),
                           'Label' : label['Name'],
                           'LabelConfidence': Decimal(str(label['Confidence']))
                          }
                    )
        ti = ti + 1


def getModerationLabels(rekognition, bucket, image, ddb, pk):
    #Unsafe content detection
    moderationLabels = rekognition.detect_moderation_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': image,
            }
        },
    )


    ti = 0

    for mlabel in moderationLabels['ModerationLabels']:
        ddbResponse = ddb.put_item(
                    Item={
                          'pk': pk,
                          'sk': '2-moderation-' + str(ti),
                           'ModerationLabel' : mlabel['Name'],
                           'ModerationLabelConfidence': Decimal(str(mlabel['Confidence']))
                          }
                    )
        ti = ti + 1

def getFaceAttributes(jsonItem, key, face):
    if(key in face):
        jsonItem[key] = face[key]['Value']
        jsonItem[key + 'Confidence'] = str(face[key]['Confidence'])

def getFaces(rekognition, bucket, image, ddb, pk):

    faces = rekognition.detect_faces(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': image,
            }
        },
        Attributes=['ALL']
    )

    print(faces)

    ti = 0

    for face in faces['FaceDetails']:

        jsonItem = {}

        jsonItem['pk'] = pk
        jsonItem['sk'] = '5-face-' + str(ti)

        #Facial Attributes
        if('AgeRange' in face):
            jsonItem['AgeRangeLow'] = face['AgeRange']['Low']
            jsonItem['AgeRangeHigh'] = face['AgeRange']['High']

        getFaceAttributes(jsonItem, 'Gender', face)
        getFaceAttributes(jsonItem, 'Smile', face)
        getFaceAttributes(jsonItem, 'Eyeglasses', face)
        getFaceAttributes(jsonItem, 'Sunglasses', face)
        getFaceAttributes(jsonItem, 'Beard', face)
        getFaceAttributes(jsonItem, 'EyesOpen', face)
        getFaceAttributes(jsonItem, 'MouthOpen', face)

        #Landmarks
        #Landmarks can be extracted like other attributes

        #Pose
        if('Pose' in face):
            jsonItem['Roll'] = str(face['Pose']['Roll'])
            jsonItem['Yaw'] = str(face['Pose']['Yaw'])
            jsonItem['Pitch'] = str(face['Pose']['Pitch'])

        #Quality
        if('Quality' in face):
            jsonItem['Brightness'] = str(face['Quality']['Brightness'])
            jsonItem['Sharpness'] = str(face['Quality']['Sharpness'])

        #item = json.dumps(jsonItem)

        ddbResponse = ddb.put_item(Item=jsonItem)

        #Emotions
        if('Emotions' in face):
            emo = 0
            emoItem = {}
            emoItem['pk'] = pk

            for emotion in face['Emotions']:
                emoItem['sk'] = '5-face-' + str(ti) + "-emotion-" + str(emo)
                emoItem['Emotion'] = emotion['Type']
                emoItem['EmotionConfidence'] = str(emotion['Confidence'])
                ddbResponse = ddb.put_item(Item=emoItem)
                emo = emo + 1

        ti = ti + 1

def getCelebrities(rekognition, bucket, image, ddb, pk):
    celebrities = rekognition.recognize_celebrities(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': image,
            }
        },
    )


    ti = 0

    for celebrity in celebrities['CelebrityFaces']:
        ddbResponse = ddb.put_item(
            Item={
                'pk': pk,
                'sk': '3-celebrity-' + str(ti),
                'CelebrityName' : celebrity['Name'],
                'CelebrityConfidence': Decimal(str(celebrity['Face']['Confidence']))
                })
        ti = ti + 1


def getText(rekognition, bucket, image, ddb, pk):

    text = rekognition.detect_text(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': image,
            }
        },
    )

    ti = 0

    for t in text['TextDetections']:
        ddbResponse = ddb.put_item(
                    Item={
                          'pk': pk,
                          'sk': '4-text-' + str(ti),
                          'Text' : t['DetectedText'],
                          'TextType': t['Type'],
                          'TextConfidence': Decimal(str(t['Confidence']))
                          }
                    )
        ti = ti + 1

# --------------- Main handler ------------------

def lambda_handler(event, context):

    # Assign S3 bucket name and DynamoDB table name from environment variables
    bucket = os.environ['BucketName']
    ddbTable = os.environ['DynamoDBTableName']

    # Get name of the image from the message on SQS queue
    image = event['Records'][0]['body']

    pk = bucket + '-' + image

    rekognition = boto3.client('rekognition', region_name='us-east-2')
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')

    ddb = dynamodb.Table(ddbTable)

    getLabels(rekognition, bucket, image, ddb, pk)
    getModerationLabels(rekognition, bucket, image, ddb, pk)
    getFaces(rekognition, bucket, image, ddb, pk)
    getCelebrities(rekognition, bucket, image, ddb, pk)
    getText(rekognition, bucket, image, ddb, pk)
