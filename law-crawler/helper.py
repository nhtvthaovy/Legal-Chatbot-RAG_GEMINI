import re

# Hàm chuyển đổi số La Mã hoặc ký tự chữ cái thành số thứ tự tương ứng
def convert_roman_to_num(roman_num):
    roman_num = roman_num.upper()
    roman_to_num = {'I': 10, 'V': 50, 'X': 100, 'L': 500, 'C': 1000, 'D': 5000, 'M': 10000}
    alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']
    num = 0
    for i in range(len(roman_num)):
        romain_char = roman_num[i]
        if romain_char not in roman_to_num.keys():
            num += alphabet.index(romain_char) + 1
            continue
        if i > 0 and roman_to_num[romain_char] > roman_to_num[roman_num[i - 1]]:
            num += roman_to_num[romain_char] - 2 * roman_to_num[roman_num[i - 1]]
        else:
            num += roman_to_num[romain_char]
    return num

# Hàm trích xuất nội dung trong dấu ngoặc đơn đầu tiên từ chuỗi
def extract_input(input_string):
    pattern = r"\((.*?)\)"  # Biểu thức chính quy để tìm nội dung trong dấu ngoặc đơn
    match = re.search(pattern, input_string)  # Tìm match đầu tiên trong chuỗi

    if match:
        return match.group(1)  # Trả về nội dung trong ngoặc đơn
    else:
        return None  # Không có gì khớp thì trả về None