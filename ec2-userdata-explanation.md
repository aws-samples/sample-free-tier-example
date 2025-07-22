# EC2 User Data Script Explanation

This document explains the EC2 user data script used in the AWS Workshop demo.

## Overview

The user data script automatically configures an EC2 instance to host a web application that connects to AWS Lambda and Amazon Bedrock. This creates a complete serverless AI demo application that launches automatically when the EC2 instance starts.

## Script Components

### 1. Initial Setup

```bash
#!/bin/bash
yum update -y
yum install -y httpd python3-pip
pip3 install boto3
systemctl start httpd
systemctl enable httpd
```

- Updates system packages
- Installs Apache web server (`httpd`) and Python pip
- Installs boto3 (AWS SDK for Python)
- Starts and enables Apache to run on boot

### 2. Web Interface Creation

The script creates an HTML file at `/var/www/html/index.html` with:
- Responsive styling (CSS)
- Input field for user questions
- Button to trigger AI requests
- Results display area
- JavaScript to handle API calls asynchronously

### 3. Backend CGI Script

```bash
mkdir -p /var/www/cgi-bin
cat > /var/www/cgi-bin/invoke-lambda.py << 'PYTHON_EOF'
# Python code here
PYTHON_EOF
chmod +x /var/www/cgi-bin/invoke-lambda.py
```

Creates a Python CGI script that:
- Handles CORS (Cross-Origin Resource Sharing)
- Processes user input from POST requests
- Invokes the Lambda function named 'workshop-demo'
- Returns the Lambda response to the web page

### 4. Apache Configuration

```bash
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

- Loads the CGI module in Apache
- Creates a URL endpoint `/invoke-lambda` that executes the Python script
- Sets appropriate permissions for the CGI directory
- Restarts Apache to apply changes

## Architecture Flow

1. User interacts with the web page hosted on EC2
2. Web page sends requests to the `/invoke-lambda` endpoint
3. CGI script on EC2 invokes the Lambda function
4. Lambda function calls Amazon Bedrock for AI processing
5. Results flow back through the same path to the user interface

This architecture demonstrates several AWS services working together:
- EC2 for web hosting
- Lambda for serverless processing
- Bedrock for AI capabilities
- IAM for secure service permissions