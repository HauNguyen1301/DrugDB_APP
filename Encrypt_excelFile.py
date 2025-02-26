import pyAesCrypt
import os

def encrypt_file(input_file, output_file, password):
    buffer_size = 64 * 1024
    pyAesCrypt.encryptFile(input_file, output_file, password, buffer_size)
    print(f"Đã mã hóa file: {input_file} → {output_file}")

def decrypt_file(input_file, output_file, password):
    buffer_size = 64 * 1024
    try:
        pyAesCrypt.decryptFile(input_file, output_file, password, buffer_size)
        print(f"Giải mã thành công: {output_file}")
    except Exception as e:
        print(f"Lỗi khi giải mã: {e}")

# Đường dẫn file gốc (có VBA)
input_file = r"G:\Bang tinh\Bang tinh v2.3.4 - for Python  DrugInfo_APP.xlsm"
encrypted_file = "encrypted.aes"  # File mã hóa sẽ có đuôi .aes
decrypted_file = "decrypted.xlsm"  # Giữ nguyên định dạng .xlsm khi giải mã
password = "123456"

# Kiểm tra file gốc trước khi mã hóa
if os.path.exists(input_file):
    encrypt_file(input_file, encrypted_file, password)
else:
    print(f"Lỗi: File {input_file} không tồn tại!")

# Giải mã lại file và giữ nguyên đuôi .xlsm
# decrypt_file(encrypted_file, decrypted_file, password)
