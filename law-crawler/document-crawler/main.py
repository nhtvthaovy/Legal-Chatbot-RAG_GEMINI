

import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
import re
from bs4 import BeautifulSoup
import requests

# Tạo kết nối với cơ sở dữ liệu
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3306/law")

# Đọc dữ liệu từ cơ sở dữ liệu
df = pd.read_sql('SELECT vbqppl_link FROM pddieu GROUP BY vbqppl_link;', con=engine)

# Khởi tạo cơ sở dữ liệu với SQLAlchemy
Base = declarative_base()

class VBPL(Base):
    __tablename__ = 'vbpl'

    id = Column(Integer, primary_key=True)
    noidung = Column(LONGTEXT, nullable=False)

# Tạo bảng nếu chưa tồn tại
Base.metadata.create_all(engine)

def get_infor(url):
    if url == None:
        return None
    match = re.search(r'ItemID=(\d+).*#(.*)', url)
    if match:
        item_id = match.group(1)
        return item_id
    else:
        print('Không tìm thấy khớp.')

def save_data(list_id, list_noidung):
    # Ghi dữ liệu vào cơ sở dữ liệu từ DataFrame
    df_to_write = pd.DataFrame({
        'id': list_id,
        'noidung': list_noidung
    })
    df_to_write.to_sql('vbpl', con=engine, if_exists='append', index=False)

list_vb = [get_infor(df.iloc[i]['vbqppl_link']) for i in range(len(df))]

print(len(df))

df_vb = pd.DataFrame(list_vb)
# Loại bỏ các giá trị None
df_vb = df_vb.dropna()
# Loại bỏ các giá trị trùng nhau
df_vb = df_vb.drop_duplicates()

print(len(df_vb))
list_id = []
list_noidung = []
for i in range(len(df_vb)):
    id = df_vb.iloc[i][0]
    print(i, "Get data id ", id)
    url_content = f'https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID={id}'
    try:
        response = requests.get(url_content, timeout=3)
        soup = BeautifulSoup(response.content, 'html.parser')
        div_text = soup.find_all('div', class_='fulltext')[0]
        noidung = div_text.find_all('div')[1]
        
        # Loại bỏ các thẻ HTML và lấy văn bản thuần túy
        noidung_text = noidung.get_text(separator=' ', strip=True)
        
        list_id.append(id)
        list_noidung.append(noidung_text)
    except:
        continue

    if i % 10 == 0:
        save_data(list_id, list_noidung)
        list_id.clear()
        list_noidung.clear()
    print("Successfully fetched and saved data for ID:", id)

# Ghi dữ liệu cuối cùng vào cơ sở dữ liệu
save_data(list_id, list_noidung)
print("Data saved successfully.")












# import pandas as pd
# from sqlalchemy import create_engine

# # Kết nối DB
# engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3306/law")

# # Đọc danh sách ID từ bảng pddieu
# df = pd.read_sql('SELECT vbqppl_link FROM pddieu GROUP BY vbqppl_link;', con=engine)

# # Hàm lấy ID từ URL
# import re
# def get_infor(url):
#     if not isinstance(url, str):  # Kiểm tra nếu url không phải là chuỗi
#         return None
#     match = re.search(r'ItemID=(\d+)', url)
#     return match.group(1) if match else None

# # Lấy danh sách ID từ bảng pddieu
# df['id'] = df['vbqppl_link'].apply(get_infor)
# df_vb = df[['id']].dropna().drop_duplicates()

# # Đọc danh sách ID đã lưu trong bảng vbpl
# existing_ids = pd.read_sql('SELECT id FROM vbpl;', con=engine)

# # Đếm số lượng ID
# count_fast = len(df_vb)  # Đếm nhanh
# count_real = len(existing_ids)  # Đếm thực tế đã lưu

# print(f"Số ID đếm nhanh: {count_fast}")
# print(f"Số ID đã lưu vào DB: {count_real}")

# # Xác định ID nào bị thiếu
# missing_ids = set(df_vb['id']) - set(existing_ids['id'])
# print(f"Số ID bị thiếu: {len(missing_ids)}")

# # Nếu muốn in danh sách ID bị thiếu
# print(missing_ids)














# import pandas as pd
# from sqlalchemy import create_engine, Column, Integer
# from sqlalchemy.dialects.mysql import LONGTEXT
# from sqlalchemy.orm import declarative_base
# import re
# from bs4 import BeautifulSoup
# import requests
# import time

# # Kết nối đến cơ sở dữ liệu MySQL
# engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3306/law")

# # Khởi tạo cơ sở dữ liệu với SQLAlchemy
# Base = declarative_base()

# class VBPL(Base):
#     __tablename__ = 'vbpl'

#     id = Column(Integer, primary_key=True)
#     noidung = Column(LONGTEXT, nullable=False)

# # Tạo bảng nếu chưa tồn tại
# Base.metadata.create_all(engine)

# def get_infor(url):
#     """Trích xuất ID từ đường link vbqppl_link"""
#     if url is None:
#         return None
#     match = re.search(r'ItemID=(\d+)', url)
#     if match:
#         return match.group(1)
#     return None

# def save_data(list_id, list_noidung):
#     """Lưu dữ liệu vào bảng vbpl"""
#     if not list_id:
#         return
#     df_to_write = pd.DataFrame({'id': list_id, 'noidung': list_noidung})
#     df_to_write.to_sql('vbpl', con=engine, if_exists='append', index=False)
#     print(f"✅ Đã lưu {len(list_id)} bản ghi vào DB.")

# # Lấy danh sách tất cả ID từ bảng pddieu
# df = pd.read_sql('SELECT vbqppl_link FROM pddieu GROUP BY vbqppl_link;', con=engine)
# list_vb = [get_infor(link) for link in df['vbqppl_link']]
# df_vb = pd.DataFrame(list_vb, columns=['id']).dropna().drop_duplicates()

# # Lấy danh sách ID đã có trong bảng vbpl
# existing_ids = pd.read_sql('SELECT id FROM vbpl;', con=engine)['id'].astype(str).tolist()

# # Lọc ra các ID còn thiếu
# missing_ids = df_vb[~df_vb['id'].astype(str).isin(existing_ids)]['id'].tolist()
# print(f"📌 Số ID cần tải lại: {len(missing_ids)}")

# # Crawl lại nội dung cho các ID bị thiếu
# list_id, list_noidung = [], []

# for i, id in enumerate(missing_ids):
#     print(f"{i+1}/{len(missing_ids)} - Get data ID {id}")
#     url_content = f'https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID={id}'
    
#     retry_count = 0
#     success = False
#     while retry_count < 3 and not success:
#         try:
#             response = requests.get(url_content, timeout=10)  # Tăng timeout lên 10 giây
#             soup = BeautifulSoup(response.content, 'html.parser')
#             div_text = soup.find_all('div', class_='fulltext')

#             if not div_text:  # Kiểm tra nếu div.fulltext không tồn tại
#                 print(f"⚠️ ID {id}: Không tìm thấy nội dung hợp lệ.")
#                 break  # Bỏ qua ID này

#             noidung_list = div_text[0].find_all('div')

#             if len(noidung_list) < 1:  # Kiểm tra nếu không đủ phần tử trong div
#                 print(f"⚠️ ID {id}: Dữ liệu không đầy đủ.")
#                 break  # Bỏ qua ID này

#             noidung = noidung_list[1]
#             list_id.append(id)
#             list_noidung.append(str(noidung))
#             success = True  # Đánh dấu lấy dữ liệu thành công

#         except requests.exceptions.Timeout:
#             retry_count += 1
#             print(f"⏳ ID {id}: Timeout, thử lại lần {retry_count}/3...")
#             time.sleep(2)  # Chờ 2 giây trước khi thử lại

#         except Exception as e:
#             print(f"⚠️ Lỗi khi lấy ID {id}: {e}")
#             break  # Bỏ qua ID này nếu lỗi khác

#     # Lưu vào DB mỗi 10 bản ghi để tránh mất dữ liệu
#     if len(list_id) % 10 == 0:
#         save_data(list_id, list_noidung)
#         list_id.clear()
#         list_noidung.clear()

# # Lưu những bản ghi còn lại
# save_data(list_id, list_noidung)
# print("🎉 Đã hoàn thành cập nhật dữ liệu còn thiếu!")

