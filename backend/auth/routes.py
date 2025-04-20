# TTTN\backend\auth\routes.py

from flask import Blueprint, request, jsonify
from .models import (
    users_collection, chat_history_collection, messages_collection,
    context_store_collection
    # , usage_logs_collection, feedback_collection
)
from .utils import hash_password, check_password, generate_token, is_valid_email, decode_token
from bson import ObjectId
from datetime import datetime
from flask import current_app as app
import time
import traceback
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DB_PERSIST_PATH = "./rag/chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

# Initialize embeddings and ChromaDB
embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})
vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

session_history = {}

auth_bp = Blueprint("auth", __name__)



# Đăng ký tài khoản
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name, email, password = data.get("name"), data.get("email"), data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Thiếu thông tin"}), 400

    if not is_valid_email(email):
        return jsonify({"error": "Email không hợp lệ"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "Email đã được đăng ký"}), 400

    hashed_password = hash_password(password)
    users_collection.insert_one({"name": name, "email": email, "password": hashed_password})

    return jsonify({"message": "Đăng ký thành công"}), 201





# Đăng nhập
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email, password = data.get("email"), data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or not check_password(password, user["password"]):
        return jsonify({"error": "Sai email hoặc mật khẩu"}), 401

    token = generate_token(str(user["_id"]))
    return jsonify({"message": "Đăng nhập thành công", "token": token}), 200






# Lấy thông tin người dùng
@auth_bp.route('/me', methods=['GET'])
def get_user_info():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user = users_collection.find_one({"_id": ObjectId(decoded["user_id"])})
    return jsonify({"name": user["name"], "email": user["email"]}), 200






# Tạo cuộc trò chuyện mới
@auth_bp.route('/conversation', methods=['POST'])
def create_conversation():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]
    data = request.get_json()
    title = data.get("title", "Cuộc trò chuyện mới")

    conversation_id = str(ObjectId())
    chat_history_collection.insert_one({"user_id": user_id, "conversation_id": conversation_id, "title": title})

    return jsonify({"status": "success", "conversation_id": conversation_id}), 201











# Sửa tiêu đề cuộc trò chuyện
@auth_bp.route('/conversation/<conversation_id>', methods=['PUT'])
def update_conversation_title(conversation_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]
    data = request.get_json() or {}
    new_title = data.get("title")

    if not new_title:
        return jsonify({"error": "Thiếu tiêu đề cuộc trò chuyện"}), 400

    # Tìm cuộc trò chuyện của user
    conversation = chat_history_collection.find_one({"conversation_id": conversation_id, "user_id": user_id})
    if not conversation:
        return jsonify({"error": "Không tìm thấy cuộc trò chuyện hoặc không có quyền"}), 404

    # Cập nhật title
    chat_history_collection.update_one(
        {"conversation_id": conversation_id, "user_id": user_id},
        {"$set": {"title": new_title}}
    )

    return jsonify({"status": "success", "message": "Cập nhật tiêu đề thành công"}), 200







# Xóa cuộc trò chuyện
@auth_bp.route('/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]

    # Tìm và xóa cuộc trò chuyện của user
    conversation = chat_history_collection.find_one({"conversation_id": conversation_id, "user_id": user_id})
    if not conversation:
        return jsonify({"error": "Không tìm thấy cuộc trò chuyện hoặc không có quyền"}), 404

    chat_history_collection.delete_one({"conversation_id": conversation_id, "user_id": user_id})
    messages_collection.delete_many({"conversation_id": conversation_id, "user_id": user_id})
    context_store_collection.delete_one({"conversation_id": conversation_id})  # Xóa ngữ cảnh liên quan

    return jsonify({"status": "success", "message": "Xóa cuộc trò chuyện thành công"}), 200







# Trả lời câu hỏi
@auth_bp.route('/question', methods=['POST'])
def handle_question():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]
    data = request.get_json() or {}
    question = data.get("question")
    conversation_id = data.get("conversation_id")

    if not question:
        return jsonify({"status": "error", "response": "Câu hỏi không được để trống."}), 400

    if not conversation_id:
        return jsonify({"status": "error", "response": "conversation_id không được để trống."}), 400

    try:
        context_doc = context_store_collection.find_one({"conversation_id": conversation_id})
        summary = context_doc["context"] if context_doc and "context" in context_doc else ""

        latest_msgs = messages_collection.find(
            {"conversation_id": conversation_id, "user_id": user_id}
        ).sort("timestamp", -1).limit(6)
        latest_msgs = list(latest_msgs)[::-1]

        recent_text = "\n".join(msg["message"] for msg in latest_msgs)
        conversation_text = f"Tóm tắt trước đó:\n{summary}\n\n6 tin nhắn mới nhất:\n{recent_text}"


    except Exception as e:
        print(f"Lỗi khi lấy lịch sử hội thoại: {e}")
        return jsonify({"status": "error", "response": "Lỗi server khi lấy lịch sử hội thoại."}), 500

    try:
        chroma_docs = vectordb.similarity_search(question, k=10)
        
        if not chroma_docs:
            return jsonify({
                "status": "error", "response": "Không tìm thấy tài liệu phù hợp trong cơ sở dữ liệu."
            }), 404

        context = "\n".join([doc.page_content for doc in chroma_docs])
        metadata = [doc.metadata for doc in chroma_docs]
       
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "response": f"Lỗi truy vấn ChromaDB: {str(e)}"}), 500

    prompt = f"""
Bạn là một trợ lý pháp lý chuyên tư vấn luật Việt Nam. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, dễ hiểu và thân thiện, dựa trên thông tin pháp lý. Sử dụng ngữ điệu tự nhiên, tránh quá khô khan nhưng vẫn đảm bảo tính chính xác.
Dựa vào lịch sử hội thoại.

Lịch sử hội thoại:
{conversation_text}

Câu hỏi:
{question}

Ngữ cảnh pháp lý:
{context}

Hãy đảm bảo câu trả lời không chỉ chính xác về mặt pháp lý mà còn dễ hiểu và mang tính ứng dụng thực tế. Nếu có thể, hãy đưa ra ví dụ hoặc giải thích thêm để người dùng dễ nắm bắt.
    """

    try:
        response = model.generate_content(prompt)
        answer = response.text.strip() if hasattr(response, "text") else "Xin lỗi, tôi không thể trả lời."
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "response": f"Lỗi từ Gemini: {str(e)}"}), 500

    def extract_info(metadata):
        ten = metadata.get("ten", "Không có tên")
        vbqppl = metadata.get("vbqppl", "")
        vbqppl_link = metadata.get("vbqppl_link", "Không có liên kết")

        return {
            "ten": ten,
            "vbqppl": vbqppl,
            "vbqppl_link": vbqppl_link
        }

    context_data = []
    
    for doc in chroma_docs:
        extracted_info = extract_info(doc.metadata)
        
        if extracted_info["ten"] != "Không có tên" and extracted_info["vbqppl_link"] != "":
            context_data.append({
                "ten": extracted_info["ten"],
                "vbqppl": extracted_info["vbqppl"],
                "vbqppl_link": extracted_info["vbqppl_link"],
            })

    try:
        messages_collection.insert_one({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message": question,
            "response": answer,
            "timestamp": datetime.utcnow(),
            "context": context_data
        })

        all_msgs = list(messages_collection.find({"conversation_id": conversation_id}).sort("timestamp", 1))

        context_text = " Câu hỏi ".join(msg["message"] for msg in all_msgs) + " Câu trả lời ".join(msg["response"] for msg in all_msgs)

        try:
            prompt_summary = f"""
            Hãy tóm tắt cuộc trò chuyện sau một cách ngắn gọn, súc tích nhưng vẫn đầy đủ thông tin quan trọng.
            Tóm tắt này sẽ được dùng để duy trì ngữ cảnh hội thoại, giúp chatbot hiểu và phản hồi chính xác hơn.           
            Cuộc trò chuyện:
            {context_text}

            """
            response_summary = model.generate_content(prompt_summary)
            summarized_context = response_summary.text.strip() if hasattr(response_summary, "text") else context_text

            context_store_collection.update_one(
                {"conversation_id": conversation_id}, 
                {"$set": {"context": summarized_context}},
                upsert=True
            )
        except Exception as e:
            print(f"Lỗi khi tóm tắt cuộc trò chuyện: {e}")
            return jsonify({"status": "error", "response": "Lỗi khi tóm tắt cuộc trò chuyện."}), 500


    except Exception as e:
        print(f"Lỗi khi lưu lịch sử hội thoại: {e}")
        return jsonify({"status": "error", "response": "Lỗi khi lưu lịch sử hội thoại."}), 500

    return jsonify({
        "status": "success",
        "question": question,
        "response": answer,
        "context": context_data,
    }), 200






# Lấy tin nhắn trong cuộc trò chuyện
@auth_bp.route('/conversation/<conversation_id>/messages', methods=['GET'])
def get_conversation_messages(conversation_id):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]

    # Fetch messages for the specified conversation
    try:
        messages = messages_collection.find({"conversation_id": conversation_id, "user_id": user_id}).sort("timestamp")
        messages_list = []
        for msg in messages:
            if "message" in msg:  # User's question
                messages_list.append({
                    "id": str(msg["_id"]),
                    "role": "user",
                    "content": msg["message"],
                    "timestamp": msg["timestamp"]
                })
            if "response" in msg:  # Assistant's response
                messages_list.append({
                    "id": str(msg["_id"]) + "_response",
                    "role": "assistant",
                    "content": msg["response"],
                    "timestamp": msg["timestamp"],
                    "context": msg.get("context", [])  # Include context if available
                })
        return jsonify({"status": "success", "messages": messages_list}), 200
    except Exception as e:
        print(f"Lỗi khi lấy tin nhắn: {e}")
        return jsonify({"status": "error", "response": "Lỗi server khi lấy tin nhắn."}), 500







# Lấy cuộc trò chuyện
@auth_bp.route('/conversations', methods=['GET'])
def get_user_conversations():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]

    # Fetch all conversations for the user
    try:
        conversations = chat_history_collection.find({"user_id": user_id}).sort("timestamp", -1)
        conversations_list = [
            {"id": conv["conversation_id"], "title": conv["title"], "date": conv.get("timestamp", datetime.utcnow()).strftime("%d/%m/%Y")}
            for conv in conversations
        ]
        return jsonify({"status": "success", "conversations": conversations_list}), 200
    except Exception as e:
        print(f"Lỗi khi lấy danh sách cuộc trò chuyện: {e}")
        return jsonify({"status": "error", "response": "Lỗi server khi lấy danh sách cuộc trò chuyện."}), 500




# Lưu phản hồi của người dùng
@auth_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    decoded = decode_token(token)
    if not decoded:
        return jsonify({"error": "Unauthorized"}), 401

    user_id = decoded["user_id"]
    data = request.get_json()
    feedback_text = data.get("feedback")

    if not feedback_text:
        return jsonify({"error": "Thiếu nội dung phản hồi"}), 400

    feedback_collection.insert_one({
        "user_id": user_id,
        "feedback": feedback_text,
        "timestamp": datetime.utcnow()
    })

    return jsonify({"status": "success"}), 201



