# config.py

import os


class Config:
    MONGO_CONNECTION_URL = os.getenv("MONGO_CONNECTION_URL", "mongodb://localhost:27017")
    LTA_API_KEY = os.getenv("LTA_API_KEY", "yMHuTv2ARJ2E4/8V6OQJWw==")
