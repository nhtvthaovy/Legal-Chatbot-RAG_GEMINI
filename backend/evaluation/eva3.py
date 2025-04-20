import time
import json
import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.chroma import Chroma
from together import Together  # Thư viện Together AI
import matplotlib.pyplot as plt

# Tải biến môi trường
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("API Key của Gemini chưa được cấu hình! Hãy kiểm tra file .env.")
if not TOGETHER_API_KEY:
    raise ValueError("API Key của LLaMA chưa được cấu hình! Hãy kiểm tra file .env.")

# Đường dẫn ChromaDB và model Sentence Transformers
DB_PERSIST_PATH = "../rag/chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

# Khởi tạo embeddings và vectordb
embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})
vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)

# Cấu hình Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Cấu hình Together AI API
client = Together(api_key=TOGETHER_API_KEY)

# Hàm lấy câu trả lời từ ChatGPT
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_chatgpt_answer(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}],
            max_tokens=150,
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Lỗi ChatGPT API: {e}")
        return "Không thể lấy câu trả lời từ ChatGPT."

# Hàm đánh giá với LLaMA
def evaluate_with_llama(prompt):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )
        return response.choices[0].message.content.strip() if response.choices else "Không có phản hồi từ LLaMA."
    except Exception as e:
        print(f"Lỗi LLaMA API khi đánh giá: {e}")
        return "Không thể đánh giá."

# Hàm lấy câu trả lời từ Gemini
def evaluate_with_retry_gemini(prompt, max_retries=3, retry_delay=30):
    retries = 0
    while retries < max_retries:
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip() if hasattr(response, "text") else "Không có kết quả đánh giá."
        except Exception as e:
            if "429" in str(e):
                print(f"Lỗi 429: Quá số lượng yêu cầu, thử lại sau {retry_delay} giây.")
                time.sleep(retry_delay)
                retries += 1
            else:
                print(f"Lỗi khác khi đánh giá: {e}")
                break
    return "Lỗi khi đánh giá"

# Hàm tạo prompt đánh giá
def get_response_evaluation_input(question, answer, context, model_name):
    return f"Bạn là giám khảo đánh giá chất lượng câu trả lời về pháp luật Việt Nam. Đánh giá câu trả lời sau đây trên thang điểm 0-100%. Chỉ trả lời một số duy nhất.\n\nCâu hỏi: {question}\nNgữ cảnh: {context}\nCâu trả lời: {answer}\n\nMô hình: {model_name}"

# Hàm thực hiện so sánh
def handle_comparison():
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        questions = data.get("questions", [])
        results = []

        for question in questions:
            print(f"Đang xử lý câu hỏi: {question}")
            chroma_docs = vectordb.similarity_search(question, k=5)
            context = "\n".join([doc.page_content for doc in chroma_docs]) if chroma_docs else ""

            # Lấy câu trả lời từ Gemini RAG
            gemini_rag_prompt = f"Bạn là trợ lý pháp lý, trả lời câu hỏi dựa trên thông tin pháp lý.\nCâu hỏi: {question}\nNgữ cảnh: {context}"
            gemini_rag_answer = evaluate_with_retry_gemini(gemini_rag_prompt)
            
            # Lấy câu trả lời từ ChatGPT No RAG
            chatgpt_no_rag_answer = get_chatgpt_answer(question)

            # LLaMA đánh giá hai mô hình
            gemini_rag_rating = evaluate_with_llama(get_response_evaluation_input(question, gemini_rag_answer, context, "Gemini RAG"))
            chatgpt_no_rag_rating = evaluate_with_llama(get_response_evaluation_input(question, chatgpt_no_rag_answer, context, "ChatGPT No RAG"))

            result = {
                "question": question,
                "gemini_rag_rating": float(gemini_rag_rating.strip('%')),
                "chatgpt_no_rag_rating": float(chatgpt_no_rag_rating.strip('%')),
            }
            results.append(result)

        df = pd.DataFrame(results)
        summary = {
            "question": "Tổng kết",
            "gemini_rag_rating": df["gemini_rag_rating"].mean(),
            "chatgpt_no_rag_rating": df["chatgpt_no_rag_rating"].mean(),
        }
        df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
        df.to_csv("evaluation_results.csv", index=False)
        print("Kết quả đã lưu vào 'evaluation_results.csv'.")

        # Vẽ biểu đồ
        df_summary = df.iloc[-1, 1:]
        df_summary.plot(kind='bar', title='So sánh Gemini RAG vs ChatGPT No RAG (LLaMA đánh giá)', xlabel='Mô hình', ylabel='Điểm số', color=['blue', 'red'])
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("gemini_vs_chatgpt_evaluation.png")
        plt.show()
    except Exception as e:
        print(f"Lỗi khi xử lý: {e}")

if __name__ == "__main__":
    handle_comparison()
