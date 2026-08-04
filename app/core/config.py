from dotenv import load_dotenv
import os

load_dotenv()
# name name from .env file or default to "JobPulse"
PROJECT_NAME = os.getenv("PROJECT_NAME", "JobPulse")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "jobpulse")