from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
MONGO_CONNECTION_STRING = os.getenv('MONGO_CONNECTION_STRING')
RIOT_API_KEY = os.getenv('RIOT_API_KEY')