# AWS Workshop - Manual Console Setup Guide

This guide walks you through setting up the workshop manually using the AWS Console. Perfect for learning each service step-by-step.

## Prerequisites
- AWS Account with admin access
- Basic familiarity with AWS Console

## Setup Time: ~20 minutes

---

## Step 1: Enable Bedrock Model Access (5 minutes)

1. Go to **Amazon Bedrock** console
2. Click **Model access** in left sidebar
3. Click **Request model access**
4. Find **Amazon Titan Text G1 - Express** and click **Request access**
5. Wait for approval (usually instant)

---

## Step 2: Create IAM Roles (5 minutes)

### Create Lambda Execution Role
1. Go to **IAM** console → **Roles**
2. Click **Create role**
3. Select **AWS service** → **Lambda**
4. Click **Next**
5. Attach policies:
   - `AWSLambdaBasicExecutionRole`
   - `AmazonBedrockFullAccess`
6. Role name: `workshop-lambda-role`
7. Click **Create role**

### Create EC2 Role
1. Click **Create role** again
2. Select **AWS service** → **EC2**
3. Click **Next**
4. Search and select: `AWSLambdaRole` (or create custom policy)
5. Role name: `workshop-ec2-role`
6. Click **Create role**
7. Click on the role → **Add permissions** → **Create inline policy**
8. JSON tab, paste:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:*:*:function:workshop-demo"
        }
    ]
}
```
9. Name: `LambdaInvokePolicy` → **Create policy**

---

## Step 3: Create Lambda Function (5 minutes)

### Create the Function
1. Go to **AWS Lambda** console
2. Click **Create function**
3. Choose **Author from scratch**
4. Function name: `workshop-demo`
5. Runtime: **Python 3.9**
6. **Change default execution role** → **Use an existing role**
7. Select: `workshop-lambda-role`
8. Click **Create function**

### Add the Code
1. In the code editor, replace all content with:

```python
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Parse input
        if 'body' in event and isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event
            
        user_input = body.get('user_input', 'Hello AWS!')
        
        # Call Bedrock
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        response = bedrock.invoke_model(
            modelId='amazon.titan-text-express-v1',
            body=json.dumps({
                "inputText": f"You are a helpful AWS assistant. Respond briefly to: {user_input}",
                "textGenerationConfig": {
                    "maxTokenCount": 100,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            })
        )
        
        ai_response = json.loads(response['body'].read())['results'][0]['outputText'].strip()
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'ai_response': ai_response,
                'timestamp': datetime.now().isoformat(),
                'user_input': user_input
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
```

2. Click **Deploy**

---

## Step 4: Launch EC2 Instance (8 minutes)

### Launch Instance
1. Go to **EC2** console
2. Click **Launch instance**
3. Name: `workshop-web-server`
4. AMI: **Amazon Linux 2** (free tier)
5. Instance type: **t2.micro** (free tier)
6. Key pair: **Proceed without a key pair**
7. **Advanced details** → **IAM instance profile** → Select `workshop-ec2-role`
8. Security group: **Create new**
   - Allow HTTP (port 80) from anywhere
9. Click **Launch instance**

### Configure Web Server
1. Wait for instance to be **Running**
2. Select the instance → **Actions** → **Connect**
3. Choose **EC2 Instance Connect** → **Connect**
4. In the terminal, run these commands:

```bash
# Install web server and Python dependencies
sudo yum update -y
sudo yum install -y httpd python3-pip
sudo pip3 install boto3
sudo systemctl start httpd
sudo systemctl enable httpd

# Create the web page
sudo tee /var/www/html/index.html > /dev/null << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AWS Workshop</title>
    <style>
        body { font-family: Arial; margin: 40px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #232f3e; text-align: center; }
        button { background: #ff9900; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px; }
        button:hover { background: #e88b00; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        #result { margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px; display: none; }
        .service { background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #ff9900; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AWS Workshop Demo</h1>
        
        <div class="service"><strong>EC2:</strong> Hosting this webpage</div>
        <div class="service"><strong>Lambda:</strong> Processing requests</div>
        <div class="service"><strong>Bedrock:</strong> AI responses</div>
        
        <hr>
        <input type="text" id="userInput" placeholder="Ask the AI something..." value="What is AWS?">
        <button onclick="callAI()">🤖 Ask AI via Lambda</button>
        
        <div id="result"></div>
    </div>
    
    <script>
        async function callAI() {
            const input = document.getElementById('userInput').value;
            const result = document.getElementById('result');
            
            result.style.display = 'block';
            result.innerHTML = '⏳ Calling Lambda + Bedrock...';
            
            try {
                const response = await fetch('/invoke-lambda', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_input: input })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    result.innerHTML = 
                        '<h3>✅ Success!</h3>' +
                        '<p><strong>You asked:</strong> ' + data.user_input + '</p>' +
                        '<p><strong>AI Response:</strong> ' + data.ai_response + '</p>' +
                        '<p><strong>Time:</strong> ' + data.timestamp + '</p>' +
                        '<hr>' +
                        '<small>🔄 Flow: Browser → EC2 → Lambda → Bedrock → Response</small>';
                } else {
                    result.innerHTML = '<h3>❌ Error:</h3><p>' + (data.error || 'Unknown error') + '</p>';
                }
            } catch (error) {
                result.innerHTML = '<h3>❌ Network Error:</h3><p>' + error.message + '</p>';
            }
        }
    </script>
</body>
</html>
EOF
```

5. **Create the Python CGI script**:
```bash
# Create CGI directory and script
sudo mkdir -p /var/www/cgi-bin
sudo tee /var/www/cgi-bin/invoke-lambda.py > /dev/null << 'PYTHON_EOF'
#!/usr/bin/env python3
import json
import boto3
import sys
import os

# Set content type
print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print()  # Empty line required

try:
    # Read POST data
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    if content_length > 0:
        post_data = sys.stdin.read(content_length)
        data = json.loads(post_data)
    else:
        data = {"user_input": "Hello AWS!"}
    
    # Invoke Lambda function
    lambda_client = boto3.client('lambda')
    
    response = lambda_client.invoke(
        FunctionName='workshop-demo',
        InvocationType='RequestResponse',
        Payload=json.dumps(data)
    )
    
    # Parse Lambda response
    lambda_response = json.loads(response['Payload'].read())
    
    if 'body' in lambda_response:
        result = json.loads(lambda_response['body'])
    else:
        result = lambda_response
    
    print(json.dumps(result))
    
except Exception as e:
    print(json.dumps({"error": str(e)}))
PYTHON_EOF

# Make script executable
sudo chmod +x /var/www/cgi-bin/invoke-lambda.py

# Configure Apache for CGI
sudo tee -a /etc/httpd/conf/httpd.conf > /dev/null << 'APACHE_EOF'

# Enable CGI
LoadModule cgi_module modules/mod_cgi.so
ScriptAlias /invoke-lambda /var/www/cgi-bin/invoke-lambda.py

<Directory "/var/www/cgi-bin">
    AllowOverride None
    Options ExecCGI
    Require all granted
</Directory>
APACHE_EOF

# Restart Apache
sudo systemctl restart httpd
```

---

## Step 5: Test Your Workshop (2 minutes)

1. Go back to **EC2** console
2. Select your instance
3. Copy the **Public IPv4 DNS**
4. Open `http://YOUR_EC2_DNS` in browser
5. Try the AI chat feature!

---

## Workshop Demo Flow

### Show Participants:
1. **EC2 Console**: Point out the running instance
2. **Lambda Console**: Show the function and recent executions
3. **Bedrock Console**: Explain model access and usage
4. **CloudWatch**: Show Lambda logs in real-time

### Interactive Demo:
1. Open the website
2. Ask different questions to the AI
3. Show responses in real-time
4. Check CloudWatch logs for each request

---

## Cleanup When Done

1. **EC2**: Terminate the instance
2. **Lambda**: Delete the function
3. **IAM**: Delete the Lambda execution role (if desired)

**Total cleanup time: 2 minutes**

---

## Troubleshooting

### Website won't load
- Wait 2-3 minutes after creating EC2 instance
- Check security group allows HTTP (port 80)

### Lambda errors
- Check CloudWatch Logs: `/aws/lambda/workshop-demo`
- Verify Bedrock permissions are attached

### Bedrock errors
- Ensure model access is granted
- Check you're using the correct region (us-east-1)

### CGI/Lambda errors
- Check Apache error logs: `sudo tail -f /var/log/httpd/error_log`
- Verify EC2 role has Lambda invoke permissions
- Check Lambda function name matches in CGI script

---

## Cost Estimate
- EC2 t2.micro: Free tier eligible
- Lambda: Free tier (1M requests/month)
- Bedrock: ~$0.01 per request

**Total workshop cost: < $0.50**