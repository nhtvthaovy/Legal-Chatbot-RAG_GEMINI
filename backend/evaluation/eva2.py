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

# Lấy API key của Gemini và LLaMA từ file .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("API Key của Gemini chưa được cấu hình! Hãy kiểm tra file .env.")
if not TOGETHER_API_KEY:
    raise ValueError("API Key của LLaMA chưa được cấu hình! Hãy kiểm tra file .env.")

# Đường dẫn cho ChromaDB và model Sentence Transformers
DB_PERSIST_PATH = "../rag/chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

# Khởi tạo các mô hình embeddings và vectordb cho ChromaDB
embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})
vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)

# Cấu hình Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# Cấu hình Together AI API
client = Together(api_key=TOGETHER_API_KEY)

# Hàm tạo prompt cho việc đánh giá câu trả lời với ngữ cảnh
def get_response_evaluation_input(question, answer, context, model_name):
    if model_name == "Gemini RAG":  # Chỉ gửi ngữ cảnh cho Gemini RAG
        return f"Bạn là người đánh giá chất lượng câu trả lời về pháp luật Việt Nam. Hãy đánh giá câu trả lời sau đây trên thang điểm từ 0 đến 100%. Chỉ trả lời một con số, không thêm bất kỳ ký tự nào khác.\n\nCâu hỏi: {question}\nNgữ cảnh pháp lý: {context}\nCâu trả lời: {answer}\n\nMô hình: {model_name}"
    else:  # Không gửi ngữ cảnh cho LLaMA (vì không có RAG)
        return f"Bạn là người đánh giá chất lượng câu trả lời về pháp luật Việt Nam. Hãy đánh giá câu trả lời sau đây trên thang điểm từ 0 đến 100%. Chỉ trả lời một con số, không thêm bất kỳ ký tự nào khác.\n\nCâu hỏi: {question}\nCâu trả lời: {answer}\n\nMô hình: {model_name}"

# Hàm lấy câu trả lời từ LLaMA API
def get_llama_answer(question):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": question}],
            max_tokens=150,
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        return "Không có phản hồi từ LLaMA."
    except Exception as e:
        print(f"Lỗi LLaMA API: {e}")
        return "Không thể lấy câu trả lời từ LLaMA."

# Hàm đánh giá với cơ chế retry cho Gemini
def evaluate_with_retry_gemini(prompt, max_retries=3, retry_delay=30):
    retries = 0
    while retries < max_retries:
        try:
            response = gemini_model.generate_content(prompt)
            return response.text.strip() if hasattr(response, "text") else "Không có kết quả đánh giá."
        except Exception as e:
            if "429" in str(e):
                print(f"Lỗi 429: Quá số lượng yêu cầu, sẽ thử lại sau {retry_delay} giây.")
                time.sleep(retry_delay)  # Chờ một khoảng thời gian trước khi thử lại
                retries += 1
            else:
                print(f"Lỗi không phải 429 khi đánh giá: {str(e)}")
                break
    return "Lỗi khi đánh giá"

# Hàm chính để thực hiện đánh giá và so sánh Gemini và LLaMA
def handle_comparison():
    try:
        # Đọc câu hỏi từ file questions.json
        with open('questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = data.get("questions", [])  # Lấy danh sách câu hỏi

        results = []

        for question in questions:
            print(f"Đang so sánh cho câu hỏi: {question}")
            
            # Truy vấn ChromaDB
            chroma_docs = vectordb.similarity_search(question, k=5)
            context = "\n".join([doc.page_content for doc in chroma_docs]) if chroma_docs else ""

            # Gemini có RAG
            start_time = time.time()
            gemini_rag_prompt = f"Bạn là một trợ lý pháp lý chuyên tư vấn luật Việt Nam. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, dễ hiểu và thân thiện, dựa trên thông tin pháp lý.\nCâu hỏi: {question}\nNgữ cảnh pháp lý: {context}"
            gemini_rag_answer = evaluate_with_retry_gemini(gemini_rag_prompt)
            gemini_rag_time = time.time() - start_time

            # LLaMA không RAG
            start_time = time.time()
            llama_no_rag_answer = get_llama_answer(question)
            llama_no_rag_time = time.time() - start_time

            # Đánh giá chất lượng từng mô hình
            gemini_rag_rating = evaluate_with_retry_gemini(get_response_evaluation_input(question, gemini_rag_answer, context, "Gemini RAG"))
            llama_no_rag_rating = evaluate_with_retry_gemini(get_response_evaluation_input(question, llama_no_rag_answer, context, "LLaMA No RAG"))

            # Lưu kết quả đánh giá
            result = {
                "question": question,
                "gemini_rag_rating": float(gemini_rag_rating.strip('%')),
                "llama_no_rag_rating": float(llama_no_rag_rating.strip('%')),
                "gemini_rag_time": gemini_rag_time,
                "llama_no_rag_time": llama_no_rag_time,
            }
            results.append(result)

        # Tính toán tổng kết trung bình
        if results:
            df = pd.DataFrame(results)

            # Thêm dòng tổng kết
            summary = {
                "question": "Tổng kết",
                "gemini_rag_rating": df["gemini_rag_rating"].mean(),
                "llama_no_rag_rating": df["llama_no_rag_rating"].mean(),
                "gemini_rag_time": df["gemini_rag_time"].mean(),
                "llama_no_rag_time": df["llama_no_rag_time"].mean(),
            }

            summary_df = pd.DataFrame([summary])  # Chuyển dòng tổng kết thành DataFrame
            df = pd.concat([df, summary_df], ignore_index=True)  # Dùng concat thay vì append

            # Lưu kết quả vào file CSV
            df.to_csv("evaluation_results.csv", index=False)
            print("Kết quả đã được lưu vào file 'evaluation_results.csv'.")

            # Vẽ biểu đồ
            df_summary = df.iloc[-1, 1:]  # Chọn dòng tổng kết
            df_summary.plot(kind='bar', title='Tổng kết Đánh giá và Thời gian', xlabel='Mô hình', ylabel='Giá trị', color=['blue', 'orange', 'green', 'red'])
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
            plt.savefig("evaluation_summary.png")  # Lưu biểu đồ vào file hình ảnh

    except Exception as e:
        print(f"Lỗi khi xử lý câu hỏi: {e}")

# Gọi hàm chính để thực hiện so sánh
if __name__ == "__main__":
    handle_comparison()
