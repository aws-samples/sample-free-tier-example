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
4. Find **Anthropic Claude 3 Haiku** and click **Request access**
5. Wait for approval (usually instant)

---

## Step 2: Create Lambda Function (8 minutes)

### Create the Function
1. Go to **AWS Lambda** console
2. Click **Create function**
3. Choose **Author from scratch**
4. Function name: `workshop-demo`
5. Runtime: **Python 3.9**
6. Click **Create function**

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
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": f"Respond briefly to: {user_input}"}]
            })
        )
        
        ai_response = json.loads(response['body'].read())['content'][0]['text']
        
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

### Add Bedrock Permissions
1. Go to **Configuration** tab → **Permissions**
2. Click the role name (opens IAM)
3. Click **Add permissions** → **Attach policies**
4. Search for `AmazonBedrockFullAccess`
5. Select it and click **Attach policy**

### Create Function URL
1. Go to **Configuration** tab → **Function URL**
2. Click **Create function URL**
3. Auth type: **NONE**
4. Configure CORS:
   - Allow origin: `*`
   - Allow methods: `POST, GET`
   - Allow headers: `*`
5. Click **Save**
6. **Copy the Function URL** - you'll need it for EC2

---

## Step 3: Launch EC2 Instance (7 minutes)

### Launch Instance
1. Go to **EC2** console
2. Click **Launch instance**
3. Name: `workshop-web-server`
4. AMI: **Amazon Linux 2** (free tier)
5. Instance type: **t2.micro** (free tier)
6. Key pair: **Proceed without a key pair**
7. Security group: **Create new**
   - Allow HTTP (port 80) from anywhere
8. Click **Launch instance**

### Configure Web Server
1. Wait for instance to be **Running**
2. Select the instance → **Actions** → **Connect**
3. Choose **EC2 Instance Connect** → **Connect**
4. In the terminal, run these commands:

```bash
# Install web server
sudo yum update -y
sudo yum install -y httpd
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
        const LAMBDA_URL = 'REPLACE_WITH_YOUR_LAMBDA_URL';
        
        async function callAI() {
            const input = document.getElementById('userInput').value;
            const result = document.getElementById('result');
            
            result.style.display = 'block';
            result.innerHTML = '⏳ Calling Lambda + Bedrock...';
            
            try {
                const response = await fetch(LAMBDA_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_input: input })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    result.innerHTML = `
                        <h3>✅ Success!</h3>
                        <p><strong>You asked:</strong> ${data.user_input}</p>
                        <p><strong>AI Response:</strong> ${data.ai_response}</p>
                        <p><strong>Time:</strong> ${data.timestamp}</p>
                        <hr>
                        <small>🔄 Flow: EC2 → Lambda → Bedrock → Response</small>
                    `;
                } else {
                    result.innerHTML = `<h3>❌ Error:</h3><p>${data.error}</p>`;
                }
            } catch (error) {
                result.innerHTML = `<h3>❌ Network Error:</h3><p>${error.message}</p>`;
            }
        }
    </script>
</body>
</html>
EOF
```

5. **Replace the Lambda URL** in the HTML:
```bash
# Replace REPLACE_WITH_YOUR_LAMBDA_URL with your actual Lambda Function URL
sudo sed -i 's|REPLACE_WITH_YOUR_LAMBDA_URL|YOUR_ACTUAL_LAMBDA_URL_HERE|g' /var/www/html/index.html
```

---

## Step 4: Test Your Workshop (2 minutes)

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

### CORS errors
- Verify Lambda Function URL has CORS configured
- Check the Lambda URL is correctly replaced in HTML

---

## Cost Estimate
- EC2 t2.micro: Free tier eligible
- Lambda: Free tier (1M requests/month)
- Bedrock: ~$0.01 per request

**Total workshop cost: < $0.50**