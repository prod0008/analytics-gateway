import boto3
import json
import os
import time
import zipfile
import io

REGION = os.getenv("AWS_REGION", "us-east-1")
iam = boto3.client('iam', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)

def create_dummy_lambda_code(name):
    code = f"""
import json
def handler(event, context):
    return {{'body': 'Mock {name} response for payload: ' + json.dumps(event)}}
"""
    zip_output = io.BytesIO()
    with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr("lambda_function.py", code)
    zip_output.seek(0)
    return zip_output.read()

print("Deploying infrastructure locally via Boto3...")

# 1. Create IAM Role
role_name = "lesson-11-agentcore-role"
try:
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        })
    )
    iam.attach_role_policy(RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
    time.sleep(10)
    role_arn = role['Role']['Arn']
except iam.exceptions.EntityAlreadyExistsException:
    role_arn = iam.get_role(RoleName=role_name)['Role']['Arn']

print(f"AGENTCORE_ROLE_ARN={role_arn}")

# 2. Create Lambda Functions
backends = ["weather", "currency", "news", "stock"]
arns = {}

for backend in backends:
    func_name = f"lesson-11-{backend}-backend"
    try:
        resp = lambda_client.create_function(
            FunctionName=func_name,
            Runtime='python3.12',
            Role=role_arn,
            Handler='lambda_function.handler',
            Code={'ZipFile': create_dummy_lambda_code(backend)},
            Timeout=30
        )
        arns[backend] = resp['FunctionArn']
    except lambda_client.exceptions.ResourceConflictException:
        arns[backend] = lambda_client.get_function(FunctionName=func_name)['Configuration']['FunctionArn']
    
    print(f"{backend.upper()}_LAMBDA_ARN={arns[backend]}")

print("\n✅ Infrastructure deployed! Copy the ARNs above into your .env file.")
