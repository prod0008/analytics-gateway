import os
import json
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

load_dotenv()

class LambdaGateway:
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.targets = {}

    def register_target(self, name: str, description: str, target_arn: str, target_type: str = "lambda"):
        self.targets[name] = {"description": description, "arn": target_arn, "type": target_type}
        print(f"[Gateway] Registered target: {name}")

    def get_tool_descriptions(self) -> str:
        if not self.targets: return "No tools currently registered."
        return "\n".join([f"- {name}: {info['description']}" for name, info in self.targets.items()])

    def invoke(self, target_name: str, payload: dict) -> str:
        if target_name not in self.targets: return f"Error: Target {target_name} not found."
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.targets[target_name]["arn"],
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            return json.loads(response['Payload'].read().decode('utf-8')).get('body', "Success")
        except Exception as e:
            return f"Error invoking {target_name}: {str(e)}"

gateway = LambdaGateway()

# TODO 1: Initialize the deterministic Bedrock model
llm = ChatBedrock(
    model_id="amazon.nova-lite-v1:0",
    model_kwargs={"temperature": 0},
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# TODO 2, 3, 4: Implement the tools
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location."""
    return gateway.invoke("weather_backend", {"location": location})

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another."""
    return gateway.invoke("currency_backend", {
        "amount": amount, 
        "from_currency": from_currency, 
        "to_currency": to_currency
    })

@tool
def get_news(topic: str) -> str:
    """Retrieve the latest news articles about a specific topic."""
    return gateway.invoke("news_backend", {"topic": topic})

# TODO 5, 6, 7: Register the backends with the gateway
gateway.register_target(
    name="weather_backend",
    description="Fetches weather data for a given location.",
    target_arn=os.getenv("WEATHER_LAMBDA_ARN"),
    target_type="lambda"
)

gateway.register_target(
    name="currency_backend",
    description="Converts currency based on current exchange rates.",
    target_arn=os.getenv("CURRENCY_LAMBDA_ARN"),
    target_type="lambda"
)

gateway.register_target(
    name="news_backend",
    description="Fetches latest news for a given topic.",
    target_arn=os.getenv("NEWS_LAMBDA_ARN"),
    target_type="lambda"
)

# TODO 8: Configure the agent with dynamic tool discovery
dynamic_tool_descriptions = gateway.get_tool_descriptions()

system_prompt = f"""You are an AI-powered analytics assistant. 
You have access to the following tools registered in the gateway:
{dynamic_tool_descriptions}

Use these tools to answer the user's queries. If a tool is not listed here, do not attempt to use it."""

tools = [get_weather, convert_currency, get_news]
agent_executor = create_react_agent(llm, tools, prompt=system_prompt)

print("\n--- Running Initial Test Queries ---")
initial_queries = [
    "What's the weather like in Seattle?",
    "Convert 100 USD to EUR.",
    "Give me the latest news on artificial intelligence."
]
for q in initial_queries:
    print(f"\nQuery: {q}")
    result = agent_executor.invoke({"messages": [("user", q)]})
    print(f"Response: {result['messages'][-1].content}")

# TODO 9: Runtime registration and testing (Stock Price)
@tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price for a given ticker symbol."""
    return gateway.invoke("stock_backend", {"ticker": ticker})

gateway.register_target(
    name="stock_backend",
    description="Fetches the current stock price for a ticker.",
    target_arn=os.getenv("STOCK_LAMBDA_ARN"),
    target_type="lambda"
)

tools.append(get_stock_price)

updated_tool_descriptions = gateway.get_tool_descriptions()
updated_system_prompt = f"""You are an AI-powered analytics assistant. 
You have access to the following tools registered in the gateway:
{updated_tool_descriptions}"""

agent_executor = create_react_agent(llm, tools, prompt=updated_system_prompt)

print("\n--- Running Runtime Test Query (Stock Price) ---")
stock_query = "What is the current stock price of AMZN?"
print(f"Query: {stock_query}")
result = agent_executor.invoke({"messages": [("user", stock_query)]})
print(f"Response: {result['messages'][-1].content}")
