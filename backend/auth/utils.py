# TTTN\backend\auth\utils.py

import bcrypt
import jwt
import datetime
import os
import re

# Lấy SECRET_KEY từ biến môi trường (dùng để mã hóa/giải mã JWT)
SECRET_KEY = os.getenv("SECRET_KEY")

# Hàm băm (hash) mật khẩu bằng bcrypt
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Hàm kiểm tra mật khẩu người dùng có khớp với mật khẩu đã băm không
def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Hàm tạo JWT token cho user đã đăng nhập
def generate_token(user_id):
    payload = {
        "user_id": user_id,  # Gắn user_id vào payload
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token hết hạn sau 1 ngày
    }
    # Trả về token được mã hóa bằng thuật toán HS256
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Hàm giải mã JWT token
def decode_token(token):
    try:
        # Giải mã token, trả về payload (thông tin người dùng)
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        print("Token đã hết hạn")  # Log lỗi token hết hạn
        return None
    except jwt.InvalidTokenError:
        print("Token không hợp lệ")  # Log lỗi token không hợp lệ
        return None

# Hàm kiểm tra định dạng email có hợp lệ hay không bằng regex
def is_valid_email(email):
    """Kiểm tra email có hợp lệ không"""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)
