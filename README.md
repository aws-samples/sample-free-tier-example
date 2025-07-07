# AWS Workshop Templates - Free Tier Examples

This repository contains CloudFormation templates and manual setup guides for AWS workshops demonstrating serverless architecture with EC2, Lambda, Aurora/DynamoDB, and Amazon Bedrock.

## 🚀 Templates Overview

### **Simple Version** (`original-simple.yaml`)
**Services:** EC2 + Lambda + Bedrock  
**Architecture:** Browser → EC2 (CGI) → Lambda → Bedrock → Response  
**Use Case:** Basic AI chat application without data persistence  
**Setup Time:** ~5 minutes  

**Features:**
- ✅ EC2 web server with Python CGI
- ✅ Lambda function with Bedrock AI integration
- ✅ Role-based security (no wildcard permissions)
- ✅ Free tier eligible
- ✅ No database - responses not stored

### **Complex Version** (`origonal-complex.yaml`)
**Services:** EC2 + Lambda + Aurora Serverless + Bedrock  
**Architecture:** Browser → EC2 (CGI) → Lambda → Bedrock + Aurora → Response  
**Use Case:** Enterprise AI chat with data persistence  
**Setup Time:** ~10 minutes  

**Features:**
- ✅ All simple version features
- ✅ Aurora Serverless MySQL database
- ✅ RDS Data API for serverless database access
- ✅ AWS Secrets Manager for credentials
- ✅ Conversation history storage
- ✅ Auto-pause database for cost optimization

## 📋 Manual Setup Guides

### **Simple Setup** (`manual-setup-guide-simple.md`)
Step-by-step console instructions for the simple version:
1. Enable Bedrock model access
2. Create IAM roles (Lambda + EC2)
3. Create Lambda function
4. Launch EC2 with UserData
5. Test the application

### **Complex Setup** (`manual-setup-guide-complex.md`)
Comprehensive guide for the complex version:
1. Enable Bedrock model access
2. Create database secret
3. Create IAM roles with RDS permissions
4. Create Aurora Serverless cluster
5. Create Lambda function with environment variables
6. Launch EC2 with UserData
7. Test with database persistence

## 🏗️ Architecture Patterns

### **Security Model**
- **EC2 Role:** Can invoke specific Lambda function only
- **Lambda Role:** Can access Bedrock and Aurora/DynamoDB
- **No wildcard permissions** or public endpoints
- **Secrets Manager** for database credentials

### **Serverless Integration**
- **EC2 UserData:** Automated setup with error handling
- **Python CGI:** Handles browser requests and AWS SDK calls
- **Lambda Functions:** Process AI requests and store data
- **Aurora Serverless:** Auto-scaling database with Data API

### **Cost Optimization**
- **Free tier eligible** components where possible
- **Aurora auto-pause** after 5 minutes of inactivity
- **Serverless architecture** scales to zero when not used
- **Estimated cost:** $0.50-$2.00 per workshop session

## 🛠️ Quick Start

### **Option 1: CloudFormation (Recommended)**
```bash
# Simple version
aws cloudformation create-stack \
  --stack-name workshop-simple \
  --template-body file://original-simple.yaml \
  --parameters ParameterKey=MyIPAddress,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_IAM

# Complex version
aws cloudformation create-stack \
  --stack-name workshop-complex \
  --template-body file://origonal-complex.yaml \
  --parameters ParameterKey=MyIPAddress,ParameterValue=YOUR_IP/32 \
  --capabilities CAPABILITY_IAM
```

### **Option 2: Manual Setup**
Follow the detailed guides:
- [Simple Manual Setup](manual-setup-guide-simple.md)
- [Complex Manual Setup](manual-setup-guide-complex.md)

## 🔧 Prerequisites

### **AWS Account Requirements**
- Admin access to AWS Console/CLI
- Amazon Bedrock model access (Titan Text Express)
- Free tier or standard billing enabled

### **Local Requirements**
- AWS CLI configured (for CloudFormation deployment)
- Your public IP address for security group access

## 📊 Workshop Demo Flow

### **For Instructors**
1. **Deploy template** 5 minutes before workshop
2. **Show AWS Console** - point out created resources
3. **Open website** - demonstrate the application
4. **Live interaction** - ask AI questions, show responses
5. **Behind the scenes** - show CloudWatch logs, database entries
6. **Architecture explanation** - discuss serverless patterns

### **For Participants**
1. **Access website** via provided URL
2. **Ask AI questions** using the chat interface
3. **See real-time responses** from Amazon Bedrock
4. **Understand flow** - browser → EC2 → Lambda → AI
5. **Explore AWS Console** - see logs and database entries

## 🐛 Troubleshooting

### **Website Won't Load**
- Wait 5-10 minutes for UserData to complete
- Check security group allows HTTP (port 80) from your IP
- Verify EC2 instance is running and has public IP

### **AI Button Shows "undefined"**
- Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)
- Check browser Developer Console (F12) for errors
- Verify Lambda function name matches in templates

### **Database Errors (Complex Version)**
- Ensure Aurora cluster status is "Available"
- Check Lambda environment variables are set correctly
- Verify RDS Data API is enabled on cluster

### **Debug Commands**
```bash
# Check UserData logs
sudo tail -f /var/log/user-data.log

# Test Apache
curl localhost

# Check Lambda logs
aws logs tail /aws/lambda/workshop-function --follow

# Test CGI script
curl -X POST localhost/invoke-lambda -d '{"user_input":"test"}'
```

## 💰 Cost Breakdown

### **Simple Version**
- EC2 t3.micro: Free tier eligible
- Lambda: Free tier (1M requests/month)
- Bedrock: ~$0.01 per request
- **Total:** < $0.50 per workshop

### **Complex Version**
- All simple version costs
- Aurora Serverless: ~$0.50/hour when active
- Secrets Manager: ~$0.40/month per secret
- **Total:** < $2.00 per workshop session

## 🧹 Cleanup

### **CloudFormation**
```bash
aws cloudformation delete-stack --stack-name workshop-simple
aws cloudformation delete-stack --stack-name workshop-complex
```

### **Manual Cleanup**
1. Terminate EC2 instances
2. Delete Lambda functions
3. Delete Aurora clusters
4. Delete IAM roles and policies
5. Delete Secrets Manager secrets

## 📚 Educational Value

### **AWS Services Demonstrated**
- **Amazon EC2:** Web hosting, UserData automation
- **AWS Lambda:** Serverless compute, event-driven architecture
- **Amazon Bedrock:** AI/ML services, model integration
- **Aurora Serverless:** Managed databases, auto-scaling
- **IAM:** Role-based security, least privilege access
- **Secrets Manager:** Credential management

### **Architecture Patterns**
- **Serverless integration** between services
- **Role-based security** without wildcard permissions
- **Event-driven architecture** with Lambda
- **Database abstraction** with RDS Data API
- **Infrastructure as Code** with CloudFormation

### **Best Practices**
- **Security:** No hardcoded credentials or public endpoints
- **Cost optimization:** Auto-pause and serverless scaling
- **Monitoring:** CloudWatch logs and error handling
- **Automation:** UserData scripts and CloudFormation

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error messages
3. Ensure all prerequisites are met
4. Verify AWS service limits and permissions

**Happy Learning! 🎓**