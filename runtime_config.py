# Load environment variables from .env file
import os

from dotenv import load_dotenv

load_dotenv()

# Access the API key
api_key = os.getenv("API_KEY")
