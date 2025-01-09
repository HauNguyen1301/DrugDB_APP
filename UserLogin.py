import base64
import socket

def xor_encrypt(input_string, key):
    # Thực hiện XOR từng ký tự với khóa
    encrypted_chars = [chr(ord(char) ^ ord(key[i % len(key)])) for i, char in enumerate(input_string)]
    # Ghép các ký tự sau khi XOR thành chuỗi
    return ''.join(encrypted_chars)

def encode_string_advanced(input_string, key):
    # Bước 1: Mã hóa XOR
    xor_encrypted = xor_encrypt(input_string, key)
    # Bước 2: Mã hóa Base64
    byte_string = xor_encrypted.encode('utf-8')
    encoded_bytes = base64.b64encode(byte_string)
    encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string

def decode_string_advanced(encoded_string, key):
    # Bước 1: Giải mã Base64
    decoded_bytes = base64.b64decode(encoded_string)
    xor_encrypted = decoded_bytes.decode('utf-8')
    # Bước 2: Giải mã XOR
    original_string = xor_encrypt(xor_encrypted, key)
    return original_string

# Lấy tên máy tính (vẫn giữ nguyên cách xử lý ban đầu)
hostname = socket.gethostname()[7:]
print(f"Tên máy tính là: {hostname}")

# Nhập chuỗi và khóa bảo mật
input_string = input("Nhập chuỗi cần mã hóa: ")
key = '13011991'

# Mã hóa
encoded_result = encode_string_advanced(input_string, key)
print(f"Chuỗi đã mã hóa: {encoded_result}")

# Giải mã để kiểm tra
decoded_result = decode_string_advanced(encoded_result, key)
print(f"Chuỗi đã giải mã: {decoded_result}")
