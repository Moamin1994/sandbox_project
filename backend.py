import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
model_name = os.getenv("MODEL_NAME")
deployment = os.getenv("DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        },
        {
            "role": "user",
            "content": input("Enter your message: "),
        }
    ],
    max_tokens=int(os.getenv("MAX_TOKENS", "1000")),
    temperature=float(os.getenv("TEMPERATURE", "1.0")),
    top_p=float(os.getenv("TOP_P", "1.0")),
    model=deployment
)

print(response.choices[0].message.content)