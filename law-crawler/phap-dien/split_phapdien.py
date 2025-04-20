import json
import os

# Đọc file gốc và xử lý JavaScript để lấy JSON
with open("phap-dien/jsonData.js", "r", encoding="utf-8") as file:
    content = file.read()

# Kiểm tra nếu file không chứa các từ khóa cần tách
if "var jdChuDe = " not in content or "var jdDeMuc = " not in content or "var jdAllTree = " not in content:
    print("Lỗi: Không tìm thấy các biến JavaScript cần thiết trong file!")
    exit()

# Tách dữ liệu dựa trên từ khóa JavaScript
try:
    jdChuDe_data = content.split('var jdChuDe = ')[1].split('var jdDeMuc = ')[0].strip().rstrip(';')
    jdDeMuc_data = content.split('var jdDeMuc = ')[1].split('var jdAllTree = ')[0].strip().rstrip(';')
    jdAllTree_data = content.split('var jdAllTree = ')[1].strip().rstrip(';')

    # Chuyển đổi chuỗi JSON thành Python dict
    jdChuDe = json.loads(jdChuDe_data)
    jdDeMuc = json.loads(jdDeMuc_data)
    jdAllTree = json.loads(jdAllTree_data)
    
except IndexError as e:
    print("Lỗi khi tách dữ liệu: Không tìm thấy phần cần thiết trong file.")
    exit()
except json.JSONDecodeError as e:
    print(f"Lỗi giải mã JSON: {e}")
    exit()

# Tạo thư mục lưu kết quả nếu chưa tồn tại
output_dir = "data-phapdien"
os.makedirs(output_dir, exist_ok=True)

# Ghi từng phần vào file JSON
with open(os.path.join(output_dir, "chude.json"), "w", encoding="utf-8") as chude_file:
    json.dump(jdChuDe, chude_file, indent=4, ensure_ascii=False)

with open(os.path.join(output_dir, "demuc.json"), "w", encoding="utf-8") as demuc_file:
    json.dump(jdDeMuc, demuc_file, indent=4, ensure_ascii=False)

with open(os.path.join(output_dir, "treeNode.json"), "w", encoding="utf-8") as tree_node_file:
    json.dump(jdAllTree, tree_node_file, indent=4, ensure_ascii=False)

print("Tách dữ liệu hoàn tất!")
