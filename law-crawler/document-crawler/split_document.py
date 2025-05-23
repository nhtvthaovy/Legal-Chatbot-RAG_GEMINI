
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine, text

# Tạo kết nối với cơ sở dữ liệu
engine = create_engine("mysql+mysqlconnector://root:123456@localhost:3306/law")

# Tạo bảng `vb_chimuc` nếu chưa tồn tại
with engine.connect() as conn:
    create_table_query = """
    CREATE TABLE IF NOT EXISTS vb_chimuc (
        id INT PRIMARY KEY,
        id_vb INT NOT NULL,
        noi_dung LONGTEXT,
        chi_muc_cha INT,
        FOREIGN KEY (chi_muc_cha) REFERENCES vb_chimuc(id)
    );
    """
    conn.execute(text(create_table_query))

# Đọc dữ liệu từ cơ sở dữ liệu
df = pd.read_sql('SELECT id, noidung FROM vbpl;', con=engine)

id = 3012
chi_muc = []
id_chuong = None

for j in range(200, len(df)):
    id_vb = df.iloc[j]['id']
    contents = df.iloc[j]['noidung']
    print(f"Đang xử lý dữ liệu cho ID {id_vb}...")
    try:
        soup = BeautifulSoup(contents, 'html.parser').find('div', id='toanvancontent')
        texts = [p.get_text().replace('\n', '').lstrip() for p in soup.find_all('p')]
    except Exception as e:
        print(f"Lỗi khi xử lý văn bản ID {id_vb}: {e}")
        continue
    
    i = 0
    text = ''
    control = 0

    def change(text, old, new):
        global id, id_chuong
        if old == 1 and new == 2:
            chi_muc.append({
                'id_vb': id_vb,
                'id': id,
                'noi_dung': text,
                'chi_muc_cha': None,
            })
        if old == 2:
            chi_muc.append({
                'id_vb': id_vb,
                'id': id,
                'noi_dung': text,
                'chi_muc_cha': id_chuong,
            })

    while i < len(texts):
        if texts[i].startswith('Chương') or texts[i].startswith('CHƯƠNG'):
            if text != '':
                change(text, control, 1)
                text = ''
            id += 1
            id_chuong = id
            control = 1
        elif texts[i].startswith('Đi'):
            if text != '':
                change(text, control, 2)
                text = ''
            id += 1
            control = 2
        text += texts[i] + '\n'
        i += 1
    
    change(text, control, 2)

# Ghi dữ liệu vào bảng `vb_chimuc`
try:
    for item in chi_muc:
        print(f"Đang ghi dữ liệu cho ID {item['id']}...")
        df_to_write = pd.DataFrame([item])
        df_to_write.to_sql('vb_chimuc', con=engine, if_exists='append', index=False)
    print("Ghi dữ liệu thành công!")
except Exception as e:  
    print(f"Lỗi khi ghi dữ liệu: {e}")
