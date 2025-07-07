# AWS Workshop - Manual Console Setup Guide (Complex Version)

This guide walks you through setting up the complex workshop manually using the AWS Console to match the `origonal-complex.yaml` template exactly. This version includes Aurora Serverless database for data persistence.

## Prerequisites
- AWS Account with admin access
- Basic familiarity with AWS Console

## Setup Time: ~25 minutes

---

## Step 1: Enable Bedrock Model Access (2 minutes)

1. Go to **Amazon Bedrock** console
2. Click **Model access** in left sidebar
3. Click **Request model access**
4. Find **Amazon Titan Text G1 - Express** and click **Request access**
5. Wait for approval (usually instant)

---

## Step 2: Create Database Secret (3 minutes)

### Create Aurora Database Secret
1. Go to **AWS Secrets Manager** console
2. Click **Store a new secret**
3. Select **Credentials for Amazon RDS database**
4. Username: `admin`
5. Click **Generate random password**
6. Click **Next**
7. Secret name: `workshop-aurora-secret`
8. Description: `Aurora database credentials`
9. Click **Next** → **Next** → **Store**

---

## Step 3: Create IAM Roles (10 minutes)

### Create Lambda Execution Role
1. Go to **IAM** console → **Roles**
2. Click **Create role**
3. Select **AWS service** → **Lambda**
4. Click **Next**
5. Search and select these policies:
   - `AWSLambdaBasicExecutionRole`
   - `AmazonBedrockFullAccess`
6. Click **Next**
7. Role name: `workshop-lambda-role`
8. Click **Create role**

### Add RDS Data API Permissions to Lambda Role
1. Click on `workshop-lambda-role`
2. Click **Add permissions** → **Create inline policy**
3. Click **JSON** tab
4. Replace content with:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds-data:ExecuteStatement",
                "rds-data:BatchExecuteStatement",
                "rds-data:BeginTransaction",
                "rds-data:CommitTransaction",
                "rds-data:RollbackTransaction"
            ],
            "Resource": "arn:aws:rds:*:*:cluster:workshop-aurora-cluster"
        },
        {
            "Effect": "Allow",
            "Action": "secretsmanager:GetSecretValue",
            "Resource": "arn:aws:secretsmanager:*:*:secret:workshop-aurora-secret*"
        }
    ]
}
```
5. Click **Next**
6. Policy name: `RDSDataAPIAccess`
7. Click **Create policy**

### Create Custom Policy for EC2
1. Go to **IAM** console → **Policies**
2. Click **Create policy**
3. Click **JSON** tab
4. Replace content with:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:*:*:function:workshop-function"
        }
    ]
}
```
5. Click **Next**
6. Policy name: `LambdaInvokePolicy`
7. Click **Create policy**

### Create EC2 Role
1. Go to **IAM** console → **Roles**
2. Click **Create role**
3. Select **AWS service** → **EC2**
4. Click **Next**
5. Search and select: 
   - `LambdaInvokePolicy`
   - `AmazonSSMManagedInstanceCore`
6. Click **Next**
7. Role name: `workshop-ec2-role`
8. Click **Create role**

---

## Step 4: Create Aurora Serverless Database (5 minutes)

### Create Aurora Cluster
1. Go to **Amazon RDS** console
2. Click **Create database**
3. Choose **Standard create**
4. Engine type: **Amazon Aurora**
5. Edition: **Amazon Aurora MySQL-Compatible Edition**
6. Capacity type: **Serverless v1**
7. DB cluster identifier: `workshop-aurora-cluster`
8. Master username: `admin`
9. Credentials management: **Manage master credentials in AWS Secrets Manager**
10. Use existing secret: Select `workshop-aurora-secret`
11. **Connectivity** → **Data API**: ✅ **Enable Data API**
12. **Additional configuration** → Initial database name: `workshop`
13. **Serverless v1 scaling configuration**:
    - Minimum Aurora capacity units: **1**
    - Maximum Aurora capacity units: **1**
    - ✅ **Pause compute capacity after consecutive minutes of inactivity**: **5 minutes**
14. Click **Create database**
15. **Wait 10-15 minutes** for database creation

---

## Step 5: Create Lambda Function (3 minutes)

### Create Lambda Function
1. Go to **AWS Lambda** console
2. Click **Create function**
3. Choose **Author from scratch**
4. Function name: `workshop-function`
5. Runtime: **Python 3.9**
6. **Change default execution role** → **Use an existing role**
7. Select: `workshop-lambda-role`
8. Click **Create function**

### Configure Environment Variables
1. Go to **Configuration** tab → **Environment variables**
2. Click **Edit** → **Add environment variable**
3. Add these variables:
   - `DB_CLUSTER_ARN`: `arn:aws:rds:us-east-1:YOUR_ACCOUNT_ID:cluster:workshop-aurora-cluster`
   - `DB_SECRET_ARN`: `arn:aws:secretsmanager:us-east-1:YOUR_ACCOUNT_ID:secret:workshop-aurora-secret-XXXXXX`
   - `DATABASE_NAME`: `workshop`
4. Click **Save**

**Note:** Replace `YOUR_ACCOUNT_ID` with your actual AWS account ID. Get the exact ARNs from the Aurora and Secrets Manager consoles.

### Add the Code
1. In the code editor, replace all content with:

```python
import json
import boto3
import os
import uuid
from datetime import datetime

def lambda_handler(event, context):
    try:
        # Parse input
        if 'body' in event and isinstance(event['body'], str):
            body = json.loads(event['body'])
        else:
            body = event
            
        user_input = body.get('user_input', 'Hello from workshop!')
        
        # Call Bedrock for AI response
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
        
        # Store in Aurora using RDS Data API
        rds_data = boto3.client('rds-data')
        
        timestamp = datetime.now().isoformat()
        interaction_id = str(uuid.uuid4())
        
        # Create table if not exists and insert data
        sql_statements = [
            "CREATE TABLE IF NOT EXISTS interactions (id VARCHAR(36) PRIMARY KEY, timestamp VARCHAR(50), user_input TEXT, ai_response TEXT)",
            f"INSERT INTO interactions (id, timestamp, user_input, ai_response) VALUES ('{interaction_id}', '{timestamp}', '{user_input.replace(\"'\", \"\\\\'\"))}', '{ai_response.replace(\"'\", \"\\\\'\")}')"
        ]
        
        for sql in sql_statements:
            rds_data.execute_statement(
                resourceArn=os.environ['DB_CLUSTER_ARN'],
                secretArn=os.environ['DB_SECRET_ARN'],
                database=os.environ['DATABASE_NAME'],
                sql=sql
            )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Success!',
                'ai_response': ai_response,
                'timestamp': timestamp,
                'stored_in': 'Aurora Serverless'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
```

2. Click **Deploy**
3. Set **Timeout** to **1 minute** in Configuration → General configuration

---

## Step 6: Launch EC2 Instance with UserData (5 minutes)

### Launch Instance
1. Go to **EC2** console
2. Click **Launch instance**
3. Name: `workshop-web-server`
4. AMI: **Amazon Linux 2** (free tier)
5. Instance type: **t2.micro** (free tier)
6. Key pair: **Proceed without a key pair**
7. Security group: **Create new**
   - Allow HTTP (port 80) from **Anywhere (0.0.0.0/0)**
   - Allow SSH (port 22) from **Anywhere (0.0.0.0/0)** (optional)
8. **Advanced details** → **IAM instance profile** → Select `workshop-ec2-role`
9. **User data** → Paste this script:

```bash
#!/bin/bash
yum update -y
yum install -y httpd python3-pip
pip3 install boto3
systemctl start httpd
systemctl enable httpd

# Create simple web page
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>AWS Workshop Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #232f3e; text-align: center; }
        .service-box { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #ff9900; }
        button { background: #ff9900; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px 5px; }
        button:hover { background: #e88b00; }
        #response { margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 5px; display: none; }
        input[type="text"] { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AWS Services Workshop</h1>
        <p>This web application demonstrates:</p>
        
        <div class="service-box">
            <strong>EC2:</strong> Hosting this web page
        </div>
        <div class="service-box">
            <strong>Lambda:</strong> Processing your requests
        </div>
        <div class="service-box">
            <strong>Aurora:</strong> Storing interaction data
        </div>
        <div class="service-box">
            <strong>Bedrock:</strong> AI-powered responses
        </div>
        
        <hr>
        <h3>Try it out!</h3>
        <input type="text" id="userInput" placeholder="Ask the AI something..." value="What is AWS?">
        <br>
        <button onclick="callLambda()">🤖 Ask AI via Lambda</button>
        <button onclick="getStats()">📊 View Workshop Info</button>
        
        <div id="response"></div>
    </div>
    
    <script>
        async function callLambda() {
            const userInput = document.getElementById('userInput').value;
            const responseDiv = document.getElementById('response');
            
            responseDiv.style.display = 'block';
            responseDiv.innerHTML = '⏳ Calling Lambda + Bedrock...';
            
            try {
                const response = await fetch('/invoke-lambda', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_input: userInput })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    responseDiv.innerHTML = 
                        '<h4>✅ Success!</h4>' +
                        '<p><strong>You asked:</strong> ' + userInput + '</p>' +
                        '<p><strong>AI Response:</strong> ' + data.ai_response + '</p>' +
                        '<p><strong>Stored at:</strong> ' + data.timestamp + '</p>' +
                        '<p><strong>Database:</strong> ' + data.stored_in + '</p>' +
                        '<hr>' +
                        '<small>🔄 Flow: Browser → EC2 → Lambda → Bedrock + Aurora → Response</small>';
                } else {
                    responseDiv.innerHTML = '<h4>❌ Error:</h4><p>' + (data.error || 'Unknown error') + '</p>';
                }
            } catch (error) {
                responseDiv.innerHTML = '<h4>❌ Network Error:</h4><p>' + error.message + '</p>';
            }
        }
        
        function getStats() {
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.innerHTML = 
                '<h4>📊 Workshop Architecture</h4>' +
                '<p>Each interaction:</p>' +
                '<ul>' +
                    '<li>Triggers a Lambda function</li>' +
                    '<li>Calls Amazon Bedrock for AI response</li>' +
                    '<li>Stores data in Aurora Serverless (MySQL database)</li>' +
                    '<li>Returns response to this EC2-hosted webpage</li>' +
                '</ul>' +
                '<p><em>Check AWS CloudWatch Logs to see Lambda executions!</em></p>';
        }
    </script>
</body>
</html>
EOF

# Create Python CGI script to invoke Lambda
mkdir -p /var/www/cgi-bin
cat > /var/www/cgi-bin/invoke-lambda.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import json
import boto3
import cgi
import cgitb
import sys
import os

# Enable CGI error reporting
cgitb.enable()

# Set content type
print("Content-Type: application/json")
print("Access-Control-Allow-Origin: *")
print("Access-Control-Allow-Methods: POST, OPTIONS")
print("Access-Control-Allow-Headers: Content-Type")
print()  # Empty line required

try:
    # Handle OPTIONS request for CORS
    if os.environ.get('REQUEST_METHOD') == 'OPTIONS':
        print(json.dumps({"status": "ok"}))
        sys.exit(0)
    
    # Read POST data
    content_length = int(os.environ.get('CONTENT_LENGTH', 0))
    if content_length > 0:
        post_data = sys.stdin.read(content_length)
        data = json.loads(post_data)
    else:
        data = {"user_input": "Hello AWS!"}
    
    # Invoke Lambda function
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    response = lambda_client.invoke(
        FunctionName='workshop-function',
        InvocationType='RequestResponse',
        Payload=json.dumps(data)
    )
    
    # Parse Lambda response
    lambda_response = json.loads(response['Payload'].read())
    
    if response['StatusCode'] == 200:
        if 'body' in lambda_response:
            # Lambda returned HTTP response format
            result = json.loads(lambda_response['body'])
        else:
            # Lambda returned direct response
            result = lambda_response
        print(json.dumps(result))
    else:
        print(json.dumps({"error": "Lambda invocation failed"}))
        
except Exception as e:
    print(json.dumps({"error": str(e)}))
PYTHON_EOF

chmod +x /var/www/cgi-bin/invoke-lambda.py

# Configure Apache for CGI
cat >> /etc/httpd/conf/httpd.conf << 'APACHE_EOF'

# Enable CGI
LoadModule cgi_module modules/mod_cgi.so
ScriptAlias /invoke-lambda /var/www/cgi-bin/invoke-lambda.py

<Directory "/var/www/cgi-bin">
    AllowOverride None
    Options ExecCGI
    Require all granted
</Directory>
APACHE_EOF

systemctl restart httpd
```

10. Click **Launch instance**

---

## Step 7: Test Your Workshop (2 minutes)

1. **Wait 5 minutes** for UserData to complete setup
2. **Ensure Aurora database is available** (check RDS console)
3. Go to **EC2** console → Select your instance
4. Copy the **Public IPv4 address** or **Public IPv4 DNS**
5. Open `http://YOUR_EC2_IP` in browser
6. Try the AI chat feature!
7. Check **RDS Query Editor** to see stored data in Aurora

**Note:** If website doesn't load immediately, wait another 2-3 minutes for UserData to finish.

---

## Workshop Demo Flow

### Show Participants:
1. **EC2 Console**: Point out the running instance
2. **Lambda Console**: Show the function and recent executions
3. **RDS Console**: Show Aurora Serverless cluster
4. **Secrets Manager**: Show database credentials
5. **Bedrock Console**: Explain model access and usage
6. **CloudWatch**: Show Lambda logs in real-time

### Interactive Demo:
1. Open the website
2. Ask different questions to the AI
3. Show responses in real-time
4. Check CloudWatch logs for each request
5. Use RDS Query Editor to show stored data

---

## Cleanup When Done

1. **EC2**: Terminate the instance
2. **Lambda**: Delete the function
3. **RDS**: Delete Aurora cluster
4. **Secrets Manager**: Delete the secret
5. **IAM**: Delete roles and policies

**Total cleanup time: 5 minutes**

---

## Troubleshooting

### Website won't load
- Wait 5 minutes after creating EC2 instance
- Check security group allows HTTP (port 80)

### Lambda errors
- Check CloudWatch Logs: `/aws/lambda/workshop-function`
- Verify all environment variables are set correctly
- Check Aurora cluster is **Available**

### Database errors
- Ensure Aurora cluster has **Data API enabled**
- Verify Lambda role has RDS Data API permissions
- Check database secret exists and is accessible

### Button shows "undefined" values
- Hard refresh browser: **Ctrl+F5** (Windows) or **Cmd+Shift+R** (Mac)
- Check browser Developer Console (F12) for JavaScript errors
- Verify Lambda function name is exactly `workshop-function`

---

## Cost Estimate
- EC2 t2.micro: Free tier eligible
- Lambda: Free tier (1M requests/month)
- Aurora Serverless: ~$0.50/hour when active (auto-pauses)
- Bedrock: ~$0.01 per request
- Secrets Manager: ~$0.40/month per secret

**Total workshop cost: < $2.00 for 1-hour session**