import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")

llm_client = AsyncOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    base_url=azure_endpoint,
)
GENERATIVE_MODEL = azure_deployment
