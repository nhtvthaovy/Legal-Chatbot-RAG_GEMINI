from flask import Blueprint, request, jsonify
import time
import traceback
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import google.generativeai as genai
from dotenv import load_dotenv
import os
from bson.json_util import dumps
from cachetools import TTLCache

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("API Key của Gemini chưa được cấu hình! Hãy kiểm tra file .env.")

DB_PERSIST_PATH = "./rag/chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})
vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# 1 ngày = 86400 giây
session_history = TTLCache(maxsize=1000, ttl=86400)

public_bp = Blueprint("public", __name__)

# Trả lời câu hỏi
@public_bp.route('/question', methods=['POST'])
def handle_question():
    data = request.get_json()
    guest_id = data.get("guest_id")
    question = data.get("question")

    if not question:
        return jsonify({"status": "error", "response": "Câu hỏi không được để trống."}), 400

    if guest_id not in session_history:
        session_history[guest_id] = []

    try:
        chroma_docs = vectordb.similarity_search(question, k=10)
        
        if not chroma_docs:
            return jsonify({
                "status": "error", "response": "Không tìm thấy tài liệu phù hợp trong cơ sở dữ liệu."
            }), 404

        context = "\n".join([doc.page_content for doc in chroma_docs])
        metadata = [doc.metadata for doc in chroma_docs]

        # print(f"Context: {context}")
        # print("Metadata:\n")
        # for doc in chroma_docs:
        #     print(doc.metadata, "\n")
    
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "response": f"Lỗi truy vấn ChromaDB: {str(e)}"}), 500

    conversation_text = "\n".join([f"User: {msg['question']}\nBot: {msg['response']}" for msg in session_history[guest_id]])
    
    prompt = f"""
Bạn là một trợ lý pháp lý chuyên tư vấn luật Việt Nam. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, dễ hiểu và thân thiện, dựa trên thông tin pháp lý.
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
        answer = response.text.strip() if hasattr(response, "text") else "Xin lỗi, tôi không thể trả lời câu hỏi này."
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

    session_history[guest_id].append({
        "question": question,
        "response": answer,
        "context": context_data  
    })

    return jsonify({
        "status": "success",
        "question": question,
        "response": answer,
        "context": context_data,  
    }), 200


