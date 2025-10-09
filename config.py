"""
Configuration file for GD Bot - Google Cloud Study Jams 2025
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_PREFIX = "."
BOT_TOKEN = os.getenv("TOKEN")
DISCORD_TOKEN = os.getenv("TOKEN")  # Alias for consistency
PREFIX = "."  # Alias for existing code compatibility

# Discord Channel IDs
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID", "1295639903463407646"))
BADGE_SUBMISSION_CHANNEL_1 = int(os.getenv("BADGE_SUBMISSION_CHANNEL_1", "1295669899078926358"))
BADGE_SUBMISSION_CHANNEL_2 = int(os.getenv("BADGE_SUBMISSION_CHANNEL_2", "1288164258638594170"))
BADGE_SUBMISSION_CHANNELS = [BADGE_SUBMISSION_CHANNEL_1, BADGE_SUBMISSION_CHANNEL_2]

# Discord Role IDs
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID", "1295638448232988713"))
COMPLETION_ROLE_ID = int(os.getenv("COMPLETION_ROLE_ID", "1296662653174808597"))

# Study Jams 2025 Configuration
TOTAL_BADGES = 20
PROGRAM_NAME = "Google Cloud Study Jams 2025"

# Badge List for Study Jams 2025
BADGE_LIST = [
    "The Basics of Google Cloud Compute",
    "Get Started with Cloud Storage",
    "Get Started with Pub/Sub",
    "Get Started with API Gateway",
    "Get Started with Looker",
    "Get Started with Dataplex",
    "Get Started with Google Workspace Tools",
    "App Building with AppSheet",
    "Develop with Apps Script and AppSheet",
    "Develop Gen AI Apps with Gemini and Streamlit",
    "Build a Website on Google Cloud",
    "Set Up a Google Cloud Network",
    "Store, Process, and Manage Data on Google Cloud - Console",
    "Cloud Run Functions: 3 Ways",
    "App Engine: 3 Ways",
    "Cloud Speech API: 3 Ways",
    "Analyze Speech and Language with Google APIs",
    "Monitoring in Google Cloud",
    "Prompt Design in Vertex AI",
    "Level 3: Generative AI"
]

# Flask Configuration (Legacy - replaced by FastAPI)
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 7083
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# FastAPI Configuration
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "30103"))
FASTAPI_DEBUG = os.getenv("FASTAPI_DEBUG", "False").lower() == "true"

# URL Pattern for Google Cloud Skills Boost
PROFILE_URL_PATTERN = r"https://www\.cloudskillsboost\.google/public_profiles/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}"
BADGE_URL_PATTERN = r"https://www\.cloudskillsboost\.google/public_profiles/\w{8}-\w{4}-\w{4}-\w{4}-\w{12}/badges/\d+"

# Production Settings
PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# API Settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100")  # requests per minute
