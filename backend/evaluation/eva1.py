import time
import json
import os
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.chroma import Chroma

# Tải biến môi trường
load_dotenv()

# Lấy API key của Gemini từ file .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("API Key của Gemini chưa được cấu hình! Hãy kiểm tra file .env.")

# Đường dẫn cho ChromaDB và model Sentence Transformers
DB_PERSIST_PATH = "../rag/chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

# Khởi tạo các mô hình embeddings và vectordb cho ChromaDB
embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})
vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)

# Cấu hình Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


# Hàm tạo prompt cho việc đánh giá retrieval
def get_retrieval_evaluation_input(question, context):
    return f"Bạn đang là người đánh giá chất lượng của một retrieval system của hệ thống pháp luật. Hãy đánh giá tri thức pháp luật ngữ cảnh retrieve được sau đây trên thang điểm từ 0 đến 100%. Chỉ trả lời một con số, không thêm bất kỳ ký tự nào khác. Ngữ cảnh: {context}\nCâu hỏi: {question}"

# Hàm tạo prompt cho việc đánh giá câu trả lời
def get_response_evaluation_input(question, answer):
    return f"Bạn là người đánh giá chất lượng câu trả lời của một LLM về pháp luật Việt Nam. Hãy đánh giá câu trả lời sau đây trên thang điểm từ 0 đến 100%. Chỉ trả lời một con số, không thêm bất kỳ ký tự nào khác. Câu hỏi: {question}\nCâu trả lời: {answer}"

# Hàm đánh giá với cơ chế retry
def evaluate_with_retry(prompt, max_retries=3, retry_delay=30):
    retries = 0
    while retries < max_retries:
        try:
            response = model.generate_content(prompt)
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

# Hàm chính để thực hiện đánh giá
def handle_evaluation():
    try:
        # Đọc câu hỏi từ file questions.json
        with open('questions.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        questions = data.get("questions", [])  # Lấy danh sách câu hỏi

        results = []
        
        # Khởi tạo các biến tính tổng và số câu hỏi đã xử lý
        total_retrieval_rating = 0
        total_response_rating = 0
        total_chroma_time = 0
        total_retrieval_time = 0
        total_gemini_time = 0
        total_response_time = 0

        for question in questions:
            print(f"Đang đánh giá câu hỏi: {question}")
            
            # Đo thời gian truy vấn ChromaDB
            start_time = time.time()
            chroma_docs = vectordb.similarity_search(question, k=2)
            chroma_time = time.time() - start_time
            if not chroma_docs:
                print(f"Lỗi: Không tìm thấy tài liệu cho câu hỏi: {question}")
                continue

            context = "\n".join([doc.page_content for doc in chroma_docs])

            # Đánh giá chất lượng retrieval
            inputs = get_retrieval_evaluation_input(question, context)
            retrieval_rating = evaluate_with_retry(inputs)

            # Sinh câu trả lời từ Gemini
            prompt = f"""
            Bạn là một trợ lý pháp lý chuyên tư vấn luật Việt Nam. Hãy trả lời câu hỏi của người dùng một cách rõ ràng, dễ hiểu và thân thiện, dựa trên thông tin pháp lý.

            Câu hỏi:
            {question}

            Ngữ cảnh pháp lý:
            {context}
            """
            gemini_answer = evaluate_with_retry(prompt)

            # Đánh giá chất lượng câu trả lời
            response_input = get_response_evaluation_input(question, gemini_answer)
            response_rating = evaluate_with_retry(response_input)

            # Cộng dồn các giá trị để tính trung bình sau này
            try:
                total_retrieval_rating += float(retrieval_rating.replace('%', '').strip()) if retrieval_rating != "Lỗi khi đánh giá" else 0
            except ValueError:
                pass  # Handle invalid ratings gracefully

            try:
                total_response_rating += float(response_rating.replace('%', '').strip()) if response_rating != "Lỗi khi đánh giá câu trả lời" else 0
            except ValueError:
                pass  # Handle invalid ratings gracefully

            total_chroma_time += chroma_time
            total_retrieval_time += time.time() - start_time  # Thời gian truy vấn ChromaDB
            total_gemini_time += time.time() - start_time  # Thời gian sinh câu trả lời từ Gemini
            total_response_time += time.time() - start_time  # Thời gian đánh giá câu trả lời

            # Lưu kết quả đánh giá và thời gian
            result = {
                "question": question,
                "retrieval_rating": f"{retrieval_rating}%",  # Thêm dấu '%' vào kết quả retrieval
                "response_rating": f"{response_rating}%",  # Thêm dấu '%' vào kết quả câu trả lời
                "chroma_time": chroma_time,
                "retrieval_time": time.time() - start_time,
                "gemini_time": time.time() - start_time,
                "response_time": time.time() - start_time,
            }
            results.append(result)
        
        # Tính trung bình các giá trị
        total_questions = len(questions)
        avg_retrieval_rating = total_retrieval_rating / total_questions if total_questions else 0
        avg_response_rating = total_response_rating / total_questions if total_questions else 0
        avg_chroma_time = total_chroma_time / total_questions if total_questions else 0
        avg_retrieval_time = total_retrieval_time / total_questions if total_questions else 0
        avg_gemini_time = total_gemini_time / total_questions if total_questions else 0
        avg_response_time = total_response_time / total_questions if total_questions else 0

        # Ghi kết quả vào file CSV
        if results:
            df = pd.DataFrame(results)
            df.to_csv('results.csv', mode='a', encoding='utf-8', index=False)

        # Ghi thông tin trung bình vào file CSV
        avg_result = {
            "question": "Tổng kết",
            "retrieval_rating": f"{avg_retrieval_rating}%",
            "response_rating": f"{avg_response_rating}%",
            "chroma_time": avg_chroma_time,
            "retrieval_time": avg_retrieval_time,
            "gemini_time": avg_gemini_time,
            "response_time": avg_response_time,
        }

        # Ghi trung bình vào file CSV
        avg_df = pd.DataFrame([avg_result])
        avg_df.to_csv('results.csv', mode='a', header=False, encoding='utf-8', index=False)

        print(f"Đánh giá {len(results)} câu hỏi thành công.")
        return

    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return

# Gọi hàm handle_evaluation để thực hiện đánh giá
if __name__ == "__main__":
    handle_evaluation()

