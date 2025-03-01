import pandas as pd
import sqlite3
import os
import gzip
import re

# Đọc dữ liệu từ file CSV chính
df = pd.read_csv('druginformation.csv', low_memory=False, dtype={'isDaRutSoDangKy': str})
 
pd.set_option('display.max_columns', None)
print(df.dtypes)  # Kiểm tra kiểu dữ liệu của các cột
print(list(df.columns)) 
df.info()  # Kiểm tra thông tin dữ liệu
print(df.iloc[:, 55].unique())  # Kiểm tra các giá trị duy nhất trong cột 55

# Trích xuất thông tin
df['soQuyetDinh'] = df['thongTinDangKyThuoc'].str.extract(r"soQuyetDinh': '([^']+)") 
df['hoatChatChinh'] = df['thongTinThuocCoBan'].str.extract(r"hoatChatChinh': '([^']+)") 
df['ngayHetHan'] = df['thongTinDangKyThuoc'].str.extract(r"ngayHetHanSoDangKy': '(\d{4}-\d{2}-\d{2})")

# Đọc dữ liệu từ file Excel vitamin
vitamin_data = pd.read_excel('Vitamin_thuoc_bo.xlsx')

# Tiền xử lý danh sách các hoạt chất
vitamin_data = vitamin_data.dropna(subset=['Ten vitamin', 'Phan loai'])
vitamin_data['Ten vitamin'] = vitamin_data['Ten vitamin'].astype(str)
vitamin_data['Dang su dung'] = vitamin_data['Dang su dung'].astype(str)

# Tạo danh sách các từ khóa vitamin từ hai cột "Ten vitamin" và "Dang su dung"
vitamin_terms = [] 
for _, row in vitamin_data.iterrows():
    if pd.notna(row['Ten vitamin']) and row['Ten vitamin'] != 'nan':
        vitamin_terms.append(row['Ten vitamin'].lower().strip())
    if pd.notna(row['Dang su dung']) and row['Dang su dung'] != 'nan':
        vitamin_terms.append(row['Dang su dung'].lower().strip())

# Loại bỏ các từ trùng lặp và chuỗi rỗng
vitamin_terms = [term for term in vitamin_terms if term and term != 'nan'] 
vitamin_terms = list(set(vitamin_terms))

# In ra một số từ khóa vitamin để kiểm tra
print("Các từ khóa vitamin đầu tiên:", vitamin_terms[:10])
print(f"Tổng số từ khóa vitamin: {len(vitamin_terms)}")

# Hàm kiểm tra xem có từ khóa vitamin nào xuất hiện trong hoạt chất không
def contains_vitamin(hoat_chat):
    if pd.isna(hoat_chat):
        return False
    
    # Tách các hoạt chất theo dấu phẩy
    hoat_chat_parts = [part.strip().lower() for part in str(hoat_chat).split(',')]
    
    # Kiểm tra từng phần của hoạt chất có khớp chính xác với các từ khóa vitamin không
    for part in hoat_chat_parts:
        if part in vitamin_terms:
            return True
            
    return False

# Kiểm tra một số mẫu hoạt chất để xem quy trình phân loại hoạt động như thế nào
sample_hoat_chat = df['hoatChatChinh'].dropna().sample(10)
for hc in sample_hoat_chat:
    print(f"Hoạt chất: {hc}")
    print(f"Chứa vitamin: {contains_vitamin(hc)}")
    print("-" * 50)

# Áp dụng phân loại
df['Phân loại'] = 'Thuốc điều trị'
df.loc[df['hoatChatChinh'].apply(contains_vitamin), 'Phân loại'] = 'Vitamin/Thuốc bổ'

# Kiểm tra kết quả phân loại
print("Thống kê phân loại:")
print(df['Phân loại'].value_counts())

# Kết nối SQLite
conn = sqlite3.connect('DrugDB.db')
df.to_sql('drugInformation', conn, if_exists='replace', index=False)
conn.close()

# Nén file SQLite
with open('DrugDB.db', 'rb') as f_in, gzip.open('DrugDB.db.gz', 'wb') as f_out:
    f_out.writelines(f_in)

print("DataFrame đã được chuyển đổi thành cơ sở dữ liệu SQLite thành công.")