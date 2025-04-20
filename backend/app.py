# TTTN\backend\app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import google.generativeai as genai
from dotenv import load_dotenv
from auth.models import messages_collection, context_store_collection, chat_history_collection
from auth.utils import decode_token
from auth.routes import auth_bp
from public.routes import public_bp  # Import the new public blueprint
import os
import traceback
import time

# Load biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for API routes


# Đăng ký blueprint auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')

# Đăng ký blueprint public_bp
app.register_blueprint(public_bp, url_prefix='/api/v1/public')

PORT = int(os.getenv("PORT", 5000))

if __name__ == '__main__': 
    app.run(debug=True, port=PORT)
