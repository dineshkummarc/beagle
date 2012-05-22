import os

# environment variables

SAFE_USERS = os.environ.get("SAFE_USERS")
FACEBOOK_SECRET = str(os.environ.get("FACEBOOK_SECRET"))
FACEBOOK_CONSUMER = str(os.environ.get("FACEBOOK_CONSUMER"))
FACEBOOK_CALLBACK = str(os.environ.get("FACEBOOK_CALLBACK"))
PORT = int(os.environ.get("PORT", 5000))
APP_SECRET_KEY = str(os.environ.get("APP_SECRET_KEY"))
DEBUG = os.environ.get("DEBUG")
DATABASE_URL=str(os.environ.get("DATABASE_URL"))
RATINGS_MULTIPLIER=str(os.environ.get("RATINGS_MULTIPLIER"))
EMAIL_USERNAME=str(os.environ.get("EMAIL_USERNAME"))
EMAIL_PASSWORD=str(os.environ.get("EMAIL_PASSWORD"))
