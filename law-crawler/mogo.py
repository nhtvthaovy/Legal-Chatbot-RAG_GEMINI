import pymysql
from pymongo import MongoClient

# Kết nối MySQL
mysql_conn = pymysql.connect(
    host='localhost',
    user='root',
    password='123456',
    database='law',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

# Kết nối MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["law_db"]  # Tạo database law_db trong MongoDB

# Lấy danh sách tất cả các bảng trong MySQL
with mysql_conn.cursor() as cursor:
    cursor.execute("SHOW TABLES;")
    tables = [list(table.values())[0] for table in cursor.fetchall()]  # Lấy tên bảng

# Lặp qua từng bảng để lấy dữ liệu và chèn vào MongoDB
for table in tables:
    with mysql_conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()

        if rows:  # Nếu có dữ liệu trong bảng
            mongo_collection = mongo_db[table]  # Tạo collection theo tên bảng
            mongo_collection.insert_many(rows)  # Nhập dữ liệu vào MongoDB
            print(f"Đã nhập {len(rows)} dòng vào MongoDB collection: {table}")

# Đóng kết nối
mysql_conn.close()
mongo_client.close()

print("Chuyển đổi dữ liệu hoàn tất!")
