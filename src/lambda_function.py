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
                            'sk': 'label-' + str(ti),
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
                          'sk': 'moderation-' + str(ti),
                           'ModerationLabel' : mlabel['Name'],
                           'ModerationLabelConfidence': Decimal(str(mlabel['Confidence']))
                          }
                    )
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
                'sk': 'celebrity-' + str(ti),
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
                          'sk': 'text-' + str(ti),
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
    getCelebrities(rekognition, bucket, image, ddb, pk)
    getText(rekognition, bucket, image, ddb, pk)