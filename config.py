import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///learning_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf'}
    LLM_API_URL = os.environ.get('LLM_API_URL') or 'http://localhost:11434/api/generate'
    LLM_MODEL ='llama3.2:3b'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024