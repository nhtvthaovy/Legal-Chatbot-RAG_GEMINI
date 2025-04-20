# TTTN\backend\common\db_connection.py

from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Kết nối MongoDB
def get_db_connection():
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database("law_db")
        print("Kết nối MongoDB thành công")
        return db
    except Exception as e:
        print(f"Lỗi kết nối MongoDB: {e}")
        return None
