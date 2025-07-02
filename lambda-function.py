import json
import boto3
import os
import uuid
from datetime import datetime

def lambda_handler(event, context):
    """
    Simple Lambda function for AWS Workshop
    - Receives user input from web page
    - Calls Amazon Bedrock for AI response
    - Stores interaction data in DynamoDB
    """
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
            
        user_input = body.get('user_input', 'Hello from AWS Workshop!')
        
        # Call Amazon Bedrock for AI response
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        prompt = f"You are a helpful AWS assistant. Respond briefly and friendly to: {user_input}"
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 150,
                "messages": [
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            })
        )
        
        # Parse Bedrock response
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        # Store in DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ.get('TABLE_NAME', 'workshop-interactions'))
        
        timestamp = datetime.now().isoformat()
        
        table.put_item(
            Item={
                'id': str(uuid.uuid4()),
                'timestamp': timestamp,
                'user_input': user_input,
                'ai_response': ai_response
            }
        )
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Workshop demo successful!',
                'ai_response': ai_response,
                'timestamp': timestamp,
                'stored_in': 'DynamoDB',
                'services_used': ['Lambda', 'Bedrock', 'DynamoDB', 'EC2']
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Workshop demo error: {str(e)}',
                'tip': 'Check CloudWatch Logs for details'
            })
        }

# For local testing
if __name__ == "__main__":
    test_event = {
        'user_input': 'Hello AWS!'
    }
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))