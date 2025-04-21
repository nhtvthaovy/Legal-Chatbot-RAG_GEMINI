import os
import json
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Định nghĩa đường dẫn
DOCS_PATH = "./law_v5"
DB_PERSIST_PATH = "./chroma_db_v5"
ST_MODEL_PATH = "keepitreal/vietnamese-sbert"

# Lấy danh sách các file JSON
json_files = [os.path.join(DOCS_PATH, f) for f in os.listdir(DOCS_PATH) if f.endswith(".json")]

def clean_metadata(metadata):
    """Lọc bỏ hoặc thay thế giá trị None trong metadata bằng chuỗi rỗng."""
    return {key: (value if value is not None else "") for key, value in metadata.items()}

def process_item(item):
    if "filename" in item and "content" in item:

    elif "noidung" in item and "ten" in item and "vbqppl" in item:

    elif "noidung" in item:

    else:
        print(f"Bỏ qua mục không hợp lệ: {item}")
        return None  # Bỏ qua nếu không khớp định dạng
    return Document(page_content=content, metadata=metadata)

# Đọc và xử lý dữ liệu
documents = []
for file_path in json_files:
    print(f"Đang đọc file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)
        if isinstance(json_data, list):
            docs = list(filter(None, (process_item(item) for item in json_data)))
            documents.extend(docs)
        elif isinstance(json_data, dict):
            doc = process_item(json_data)
            if doc:
                documents.append(doc)
    
    # Chia nhỏ văn bản cho từng file
    text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=0, separator="\n")
    split_texts = text_splitter.split_documents(documents)
    print(f"File {os.path.basename(file_path)} có {len(split_texts)} đoạn.")

total_splits = sum(len(text_splitter.split_documents(documents)) for file_path in json_files)
print(f"Tổng số đoạn sau khi chia nhỏ: {total_splits}")

# Tạo embeddings
embeddings = HuggingFaceEmbeddings(model_name=ST_MODEL_PATH, model_kwargs={"device": "cpu"})

# Khởi tạo hoặc cập nhật ChromaDB
if os.path.exists(DB_PERSIST_PATH):
    print("Đang cập nhật dữ liệu vào ChromaDB...")
    vectordb = Chroma(persist_directory=DB_PERSIST_PATH, embedding_function=embeddings)
    vectordb.add_documents(documents=documents)
else:
    print("Đang tạo mới ChromaDB...")
    vectordb = Chroma.from_documents(documents=documents, embedding=embeddings, persist_directory=DB_PERSIST_PATH)

print("Dữ liệu JSON đã được vector hóa và lưu trữ thành công!")
