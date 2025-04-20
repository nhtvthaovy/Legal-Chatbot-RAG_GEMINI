
# TTTN\backend\auth\models.py

from common.db_connection import get_db_connection


# Kết nối tới MongoDB
db = get_db_connection()

# Định nghĩa các collection (bảng)
if db is not None:
    users_collection = db.get_collection("users")
    chat_history_collection = db.get_collection("chat_history")
    messages_collection = db.get_collection("messages")
    context_store_collection = db.get_collection("context_store")

else:
    users_collection = None
    chat_history_collection = None
    messages_collection = None
    context_store_collection = None


