import pandas as pd
import sqlite3
import os
import gzip

df = pd.read_csv('druginfomation.csv')
df['soQuyetDinh'] = df['thongTinDangKyThuoc'].str.extract(r"'soQuyetDinh': '([^']+)'")
df['hoatChatChinh'] = df['thongTinThuocCoBan'].str.extract(r"'hoatChatChinh': '([^']+)'")
df['ngayHetHan'] = df['thongTinDangKyThuoc'].str.extract(r"'ngayHetHanSoDangKy': '(\d{4}-\d{2}-\d{2})")
conn = sqlite3.connect('DrugDB.db')
df.to_sql('drugInformation', conn, if_exists='replace', index=False)
conn.close()
with open('DrugDB.db', 'rb') as f_in, gzip.open('DrugDB.db.gz', 'wb') as f_out:
    f_out.writelines(f_in)


print("DataFrame successfully converted to SQLite database.")