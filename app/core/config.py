from dotenv import load_dotenv
import os

load_dotenv()
# name
PROJECT_NAME = os.getenv("PROJECT_NAME", "JobPulse")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "jobpulse")