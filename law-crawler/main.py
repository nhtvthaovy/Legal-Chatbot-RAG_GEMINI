

from models.models import *
from bs4 import BeautifulSoup
from helper import *
import os
import json
import uuid

# CREATE-DROP Tất cả dữ liệu
db.drop_tables([PDMucLienQuan, PDTable, PDFile, PDDieu, PDChuong, PDDeMuc, PDChuDe])
db.create_tables([PDMucLienQuan, PDTable, PDFile, PDDieu, PDChuong, PDDeMuc, PDChuDe])

# Tạo file log
log_file = open("log.txt", "w", encoding="utf-8")

def log(message):
    log_file.write(message + "\n")
    print(message)

# Đọc Chủ đề
log("Load Chủ Đề Từ File ...")
with open("./data-phapdien/chude.json", "r", encoding="utf-8") as chude_file:
    chudes = json.load(chude_file)

log("Insert tất cả chủ đề...")
try:
    with db.atomic():
        PDChuDe.bulk_create([PDChuDe(ten=chude["Text"], stt=chude["STT"], id=chude["Value"]) for chude in chudes])
    log("Inserted tất cả chủ đề pháp điển!")
except Exception as e:
    log(f"Lỗi khi insert chủ đề: {str(e)}")

# Đọc Đề mục
log("Load Đề Mục Từ File ...")
with open("./data-phapdien/demuc.json", "r", encoding="utf-8") as demuc_file:
    demucs = json.load(demuc_file)

log("Insert tất cả đề mục...")

# Insert danh sách đề mục vào DB
try:
    with db.atomic():  # Dùng transaction để đảm bảo tính toàn vẹn
        PDDeMuc.bulk_create(
            [PDDeMuc(ten=demuc["Text"], stt=demuc["STT"], id=demuc["Value"], chude_id=demuc["ChuDe"]) for demuc in demucs]
        )
    log("Inserted tất cả đề mục pháp điển!")
except Exception as e:
    log(f"Lỗi khi insert đề mục: {str(e)}")

log("Load Tree Nodes Từ File ...")

# Load dữ liệu cấu trúc cây (tree node) từ file JSON
with open("./data-phapdien/treeNode.json", "r", encoding="utf-8") as tree_nodes_file:
    tree_nodes = json.load(tree_nodes_file)

log("Insert tất cả nodes...")

# Duyệt qua thư mục chứa các file đề mục HTML
demuc_directory = os.fsencode("./data-phapdien/demuc")
dieus_lienquan = []
count = 0

for file in os.listdir(demuc_directory):
    file_name = os.fsdecode(file)
    with open(f"./data-phapdien/demuc/{file_name}", "r", encoding="utf-8") as demuc_file:
        count += 1
        # Đọc nội dung file HTML đề mục và phân tích cú pháp bằng BeautifulSoup
        # Sử dụng bộ phân tích 'html.parser' để chuyển đổi nội dung thành cây DOM có thể truy vấn
        demuc_html = BeautifulSoup(demuc_file.read(), "html.parser")

        # Lấy danh sách node tương ứng với đề mục đang xử lý
        demuc_nodes = [node for node in tree_nodes if node["DeMucID"] == file_name.split(".")[0]]

        # Tách riêng các node là Chương
        demuc_chuong = [node for node in demuc_nodes if node["TEN"].startswith("Chương ")]
        chuongs_data = []

        for chuong in demuc_chuong:
            mapc = chuong["MAPC"]
            stt = convert_roman_to_num(chuong["ChiMuc"])  # Chuyển số La Mã thành số thường
            chuong_data = PDChuong(ten=chuong["TEN"], mapc=mapc, chimuc=chuong["ChiMuc"], stt=stt, demuc_id=chuong["DeMucID"])
            
            # Insert chương vào DB
            try:
                PDChuong.create(**chuong_data.__dict__)
            except:
                continue
            chuongs_data.append(chuong_data)

        log(f'Insert {len(demuc_chuong)} chương của đề mục {file_name}')

        # Nếu không có chương nào, tạo một chương mặc định
        if len(chuongs_data) == 0:
            chuong_data = PDChuong(ten="", mapc=uuid.uuid4(), chimuc="0", stt=0, demuc_id=file_name.split(".")[0])
            chuongs_data.append(chuong_data)

        # Các node còn lại là Điều
        demuc_dieus = [node for node in demuc_nodes if node not in demuc_chuong]
        log(f'Đề mục {file_name} có {len(demuc_chuong)} chương và {len(demuc_dieus)} điều')

        stt = 0
        for dieu in demuc_dieus:
            # Gán Điều vào Chương phù hợp
            if len(chuongs_data) == 1:
                dieu["ChuongID"] = chuongs_data[0].mapc
            else:
                for chuong in chuongs_data:
                    if dieu["MAPC"].startswith(chuong.mapc):
                        dieu["ChuongID"] = chuong.mapc
                        break

            # Trích xuất nội dung Điều từ HTML
            mapc = dieu["MAPC"]
            dieu_html = demuc_html.select(f'a[name="{mapc}"]')[0]
            ten = dieu_html.nextSibling
            ghi_chu_html = dieu_html.parent.nextSibling
            vbqppl = ghi_chu_html.text if ghi_chu_html else None
            vbqppl_link = ghi_chu_html.select("a")[0]["href"] if ghi_chu_html.select("a") else None

            # Lấy đoạn nội dung chính
            noidung_html = dieu_html.parent.find_next("p", {"class": "pNoiDung"})
            noidung = ""
            tables = []

            for content in noidung_html.contents:
                if content.name == "table":
                    tables.append(str(content))
                    continue
                noidung += str(content.text.strip()) + "\n"

            # Insert Điều
            try:
                PDDieu.create(
                    ten=ten,
                    mapc=mapc,
                    chimuc=dieu["ChiMuc"],
                    stt=stt,
                    noidung=noidung,
                    vbqppl=vbqppl,
                    vbqppl_link=vbqppl_link,
                    chude_id=dieu["ChuDeID"],
                    demuc_id=dieu["DeMucID"],
                    chuong_id=dieu["ChuongID"]
                )
            except:
                continue

            # Insert các bảng liên quan trong nội dung Điều
            for table in tables:
                PDTable.create(dieu_id=mapc, html=table)

            # Tìm các file đính kèm
            element = noidung_html.nextSibling
            while element and element.name == "a":
                link = element["href"]
                try:
                    PDFile.create(dieu_id=dieu["MAPC"], link=link, path="")
                except:
                    log(f"Lỗi insert file {link}")
                element = element.nextSibling

            # Xử lý các Điều liên quan
            if element and element.name == "p" and element.get("class") and element["class"][0] == "pChiDan":
                lienquans_html = element.select("a")
                for lienquan_html in lienquans_html:
                    if "onclick" not in lienquan_html.attrs or lienquan_html["onclick"] == "":
                        continue
                    mapc_lienquan = extract_input(lienquan_html["onclick"]).replace("'", "")
                    dieus_lienquan.append({
                        "dieu_id1": dieu["MAPC"],
                        "dieu_id2": mapc_lienquan
                    })

            stt += 1

log("Inserted tất cả nodes pháp điển!")

# Insert quan hệ Điều liên quan
for dieu_lienquan in dieus_lienquan:
    try:
        PDMucLienQuan.create(
            dieu_id1=dieu_lienquan["dieu_id1"],
            dieu_id2=dieu_lienquan["dieu_id2"]
        )
    except:
        log(f'Không thể insert liên quan {dieu_lienquan["dieu_id1"]} - {dieu_lienquan["dieu_id2"]}')
    log(f'Inserted liên quan {dieu_lienquan["dieu_id1"]} - {dieu_lienquan["dieu_id2"]}')

log_file.close()
