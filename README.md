# AI Analytics Assistant with Gateway Pattern

An AI-powered analytics assistant that uses a gateway pattern to dynamically discover and route requests to backend Lambda functions.

## Features
- Dynamic tool discovery via AgentCore Gateway
- Runtime tool registration (no code changes needed for new backends)
- Deterministic Bedrock model for reliable routing
- Lambda-based backend services

## Setup
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install boto3 python-dotenv langchain langchain-aws langchain-core langgraph

# Deploy infrastructure
python3 infrastructure/deploy_stack.py

# Update .env with ARNs, then run:
python3 analytics_gateway.py
\`\`\`

## Cleanup
\`\`\`bash
python3 infrastructure/cleanup.py
\`\`\`
