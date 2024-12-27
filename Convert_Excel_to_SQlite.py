import pandas as pd
import sqlite3
import os

# Step 1: Load the Excel file into a DataFrame
excel_file = r"F:\PBI Ban\Python Project\Crawl Drugbank\Drugbank_DB.xlsx"  # Replace with your file name
sheet_name = "Sheet1"  # Replace with your sheet name if necessary
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# Step 2: Connect to an SQLite database (or create one if it doesn't exist)

# Step 2: Đặt đường dẫn đến thư mục lưu file SQLite
output_dir = r"F:\PBI Ban\Python Project\Crawl Drugbank"  # Thư mục đích
sqlite_db = os.path.join(output_dir, "drugDB.sqlite")  # Tên file SQLite
conn = sqlite3.connect(sqlite_db)


# Step 3: Write the DataFrame to an SQLite table
table_name = "druginfo"  # Replace with your desired table name
df.to_sql(table_name, conn, if_exists="replace", index=False)

# Step 4: Close the database connection
conn.close()

print(f"Data successfully written to {sqlite_db} in table '{table_name}'.")
