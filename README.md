# rekognition-sqs

Using SQS as an event source, trigger a Lambda function to perform image analysis using Amazon Rekognition and write the output to a DynamoDB table.



## Using SQS as an event source to trigger Lambda

This repository contains an AWS Lambda function that uses SQS as an event source.

- An image is uploaded to a S3 bucket
- Image name is written to a SQS queue
- The SQS message triggers a Lambda function
- Lambda invokes Rekognition APIs for celebrity and text detection on that image
- Lambda writes the output to a DynamoDB table.  

### Prerequisites
- An AWS Account with permissions to IAM, CloudFormation, S3, SQS, Lambda, Rekognition, and DynamoDB.
- Install AWS CLI and configure the credentials.
- Git client  

### Steps to deploy this application
Please note:   
a. We will be using the us-east-2 region (Ohio) for deploying this application.  
b. User-specified input parameters will be marked with curly braces in the following instructions. For e.g., {s3-bucket-name} will need to be replaced with a bucket name of your choice, such as mybucketname etc.  


#### Steps
1. Clone this repo and change to the directory 'rekognition-sqs'.  
  
2. Create a SQS queue for publishing the image name. Set the VisibilityTimeout attribute to 3000 seconds. Note down the queue name to be used in step 5 below.  
	*aws sqs create-queue --queue-name {SQS_queue_name} --region us-east-2 --attributes VisibilityTimeout=3000*  

3. Create a S3 bucket for storing SAM deployment artifacts in the us-east-2 region. Please note that you may not use '-' or '.' in your bucket name.  
	*aws s3 mb s3://{s3-bucket-name} --region us-east-2*  
      
4. Create the Serverless Application Model package using CLI.  
	*aws cloudformation package \  
	--region us-east-2 \  
	--template-file template.yml \  
	--s3-bucket {image_bucket_name} \  
	--output-template-file build/packaged-template.yml*  
      
5. Deploy the packaged template. Enter input parameters for the S3 bucket name (given in step 3 above), DynamoDB table name, and SQS queue name (from step 2 above). This step will create a DynamoDB table, and a S3 bucket using the names specified. It will also create a Lambda function with the name 'SQSLambda'.  
	*aws cloudformation deploy \  
	--region us-east-2 \  
	--template-file build/packaged-template.yml \  
	--stack-name {stack_name} \  
	--parameter-overrides BUCKETNAME={image_bucket_name} TABLENAME={DynamoDB_table_name} QUEUENAME={SQS_queue_name} \  
	--capabilities CAPABILITY_IAM*  
  
6. After the stack has been successfully created, from the AWS Console for SQS, add a Queue Action for the queue created in Step 2. The queue action is 'Configure Trigger for Lambda Function', and select the 'SQSLambda' function in the drop down list.  

#### Testing the application
1. Post an image of your favorite celebrity with some text in the image, to the S3 bucket created in Step 5 as part of application deployment above.  
2. Post the image file name to the SQS queue created in Step 5 above.  
3. The Lambda execution should take about 20-30 seconds. Observe the results of the execution in the DynamoDB table. 