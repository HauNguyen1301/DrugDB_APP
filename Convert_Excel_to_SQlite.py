import pandas as pd
import sqlite3
import os
import gzip

# Đọc dữ liệu từ file CSV chính
df = pd.read_csv('druginformation.csv')

df['soQuyetDinh'] = df['thongTinDangKyThuoc'].str.extract(r"soQuyetDinh': '([^']+)")
df['hoatChatChinh'] = df['thongTinThuocCoBan'].str.extract(r"hoatChatChinh': '([^']+)")
df['ngayHetHan'] = df['thongTinDangKyThuoc'].str.extract(r"ngayHetHanSoDangKy': '(\d{4}-\d{2}-\d{2})")

# Đọc dữ liệu từ file Excel vitamin
vitamin_data = pd.read_excel('Vitamin_thuoc_bo.xlsx')

# Tra cứu và thêm cột "Phân loại" dựa trên hoatChatChinh
def map_category(row):
    hoat_chat_chinh = str(row['hoatChatChinh']) if not pd.isna(row['hoatChatChinh']) else ""
    for _, vitamin_row in vitamin_data.iterrows():
        ten_vitamin = str(vitamin_row['Ten vitamin']) if not pd.isna(vitamin_row['Ten vitamin']) else ""
        dang_su_dung = str(vitamin_row['Dang su dung']) if not pd.isna(vitamin_row['Dang su dung']) else ""
        if ten_vitamin in hoat_chat_chinh or dang_su_dung in hoat_chat_chinh:
            return vitamin_row['Phan loai']
    return "Nhóm thuốc điều trị"

df['Phân loại'] = df.apply(map_category, axis=1)

# Kết nối SQLite
conn = sqlite3.connect('DrugDB.db')
df.to_sql('drugInformation', conn, if_exists='replace', index=False)
conn.close()

# Nén file SQLite
with open('DrugDB.db', 'rb') as f_in, gzip.open('DrugDB.db.gz', 'wb') as f_out:
    f_out.writelines(f_in)

print("DataFrame successfully converted to SQLite database.")
