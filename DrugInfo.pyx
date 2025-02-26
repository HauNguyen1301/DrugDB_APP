import tkinter as tk
from tkinter import ttk
import gzip
import io, os
import sqlite3
import tempfile
from tkinter import messagebox
from typing import List, Tuple
import pyperclip  # Add this import at the top of your file
import socket
import base64
from datetime import datetime
import subprocess
from tkinter import IntVar
import pyAesCrypt
import win32com.client


KEY_TEMP = "17121991"
def get_current_quarter():
    """Lấy quý hiện tại và trả về năm + '1' cho quý 1-2, năm + '2' cho quý 3-4."""
    current_month = datetime.now().month
    current_year = datetime.now().year
    quarter = (current_month - 1) // 3 + 1
    return f"{current_year}{'1' if quarter <= 2 else '2'}"

def generate_dynamic_key():
    """Tạo key động bằng cách kết hợp GLOBAL_ENCRYPTION_KEY với năm hiện tại."""
    return KEY_TEMP + get_current_quarter()

GLOBAL_ENCRYPTION_KEY = generate_dynamic_key()
print("Key hiện tại:", GLOBAL_ENCRYPTION_KEY)

# Test key


class FormattedEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind('<KeyRelease>', self.format_number)
        self.bind('<<Paste>>', self.on_paste)
        self.variable = kwargs.get('textvariable') or tk.StringVar()
        self.variable.trace('w', self.format_number)
        self.configure(textvariable=self.variable)
        self.configure(validate="key")
        self.configure(validatecommand=(self.register(self.validate_numeric), '%P'))
        # Thêm biến để theo dõi vị trí con trỏ
        self.cursor_position = 0

    def format_number(self, *args):
        # Lưu vị trí con trỏ hiện tại
        try:
            self.cursor_position = self.index(tk.INSERT)
        except:
            self.cursor_position = 0
            
        value = self.variable.get().replace(' ', '')  # Xóa khoảng trắng
        
        if value.isdigit():
            # Đếm số ký tự khoảng trắng trước vị trí con trỏ
            original_text = self.variable.get()
            spaces_before_cursor = len([c for c in original_text[:self.cursor_position] if c == ' '])
            
            # Định dạng số
            formatted = ' '.join([value[max(i-3, 0):i] for i in range(len(value), 0, -3)][::-1])
            
            # Đặt giá trị mới
            self.variable.set(formatted)
            
            # Tính toán vị trí con trỏ mới
            new_spaces = len([c for c in formatted[:self.cursor_position + spaces_before_cursor] if c == ' '])
            new_position = self.cursor_position + (new_spaces - spaces_before_cursor)
            
            # Đặt lại vị trí con trỏ sau khi định dạng
            self.after(0, lambda: self.icursor(new_position))

    def validate_numeric(self, text):
        return text == "" or text.replace(' ', '').isdigit()

    def on_paste(self, event):
        clipboard = self.clipboard_get()
        # Remove non-numeric characters
        numeric_only = ''.join(filter(str.isdigit, clipboard))
        if numeric_only:
            self.delete(0, tk.END)
            self.insert(0, numeric_only)
            
            # Định dạng số với khoảng trắng
            formatted = ' '.join([numeric_only[max(i-3, 0):i] 
                                for i in range(len(numeric_only), 0, -3)][::-1])
            
            # Đặt giá trị mới
            self.variable.set(formatted)
            
            # Di chuyển con trỏ đến cuối
            self.after(0, lambda: self.icursor(len(formatted)))
        
        return 'break'  # Prevent default paste behavior


class DrugSearchApp:
    
    # def validate_key(self):
    #     try:
    #         # Lấy hostname của máy
    #         hostname = socket.gethostname()[7:]
    #         # Mã hóa hostname bằng base64
    #         encoded_hostname = base64.b64encode(hostname.encode()).decode()
    #         # Lấy key người dùng nhập vào
    #         user_key = self.key_var.get()
            
    #         # So sánh key
    #         if user_key == encoded_hostname:
    #             return True
    #         return False
    #     except Exception as e:
    #         print(f"Lỗi kiểm tra key: {e}")
    #         return False
    def close_connection(self):
        """Đóng kết nối database."""
        try:
            if hasattr(self, 'cursor'):
                self.cursor.close()
                print("Đóng cursor.")

            if hasattr(self, 'conn'):
                self.conn.close()
                print("Đóng kết nối database.")
        except Exception as e:
            print(f"Lỗi khi đóng kết nối: {e}")
    def on_close(self):
        """Đóng kết nối database và xóa file tạm khi ứng dụng đóng."""
        self.close_connection()

        try:
            if hasattr(self, 'temp_db_path') and os.path.exists(self.temp_db_path):
                import time
                time.sleep(0.5)  # Đợi một chút để hệ thống giải phóng file

                os.remove(self.temp_db_path)
                print("Đã xóa file database tạm thời.")
        except Exception as e:
            print(f"Lỗi khi đóng ứng dụng: {e}")

        self.root.destroy()



    def xor_encrypt(self, input_string, key):
        """Perform XOR encryption on the input string using the given key."""
        encrypted_chars = [chr(ord(char) ^ ord(key[i % len(key)])) for i, char in enumerate(input_string)]
        return ''.join(encrypted_chars)

    def encode_string_advanced(self, input_string, key):
        """Encode the input string using XOR encryption and Base64 encoding."""
        xor_encrypted = self.xor_encrypt(input_string, key)
        byte_string = xor_encrypted.encode('utf-8')
        encoded_bytes = base64.b64encode(byte_string)
        return encoded_bytes.decode('utf-8')

    def decode_string_advanced(self, encoded_string, key):
        """Decode the encoded string using Base64 decoding and XOR decryption."""
        decoded_bytes = base64.b64decode(encoded_string)
        xor_encrypted = decoded_bytes.decode('utf-8')
        return self.xor_encrypt(xor_encrypted, key)

    def validate_key(self):
        """Validate the user-entered key against the encrypted hostname."""
        try:
            # Get the hostname of the machine
            full_hostname = socket.gethostname()
            current_month = datetime.now().month  # Lấy tháng hiện tại (1-12)
            current_year = datetime.now().year  # Lấy năm hiện tại
            if full_hostname[:4] == "GTSC":
                hostname = full_hostname[7:].upper()
            else:
                hostname = full_hostname.upper()
            
            # Use a fixed key for encryption (you can change this to a more secure key)
            encryption_key = GLOBAL_ENCRYPTION_KEY
            
            # Encode the hostname using the advanced method
            encoded_hostname = self.encode_string_advanced(hostname, encryption_key)
            
            # Get the key entered by the user
            user_key = self.key_var.get()
            
            # Compare the keys
            if user_key == encoded_hostname or (full_hostname == "GTSC1D1HAUNH0" and user_key == "22"):
                return True
            elif current_month in [2, 3, 4, 5] and current_year in [2025] and user_key == "123456":
                return True    
            return False
        except Exception as e:
            print(f"Error validating key: {e}")
            return False




    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Tra cứu Thuốc - v1.7.1.0")
        self.root.tk.call('tk', 'scaling', 1.25)
        self.create_widgets()
        self.info_label_var = tk.StringVar()
        # Initialize previous search variables
        self.prev_brand_search = ""
        self.prev_ingredient_search = ""
        self.discount_var = tk.StringVar(value="20")  # Default to 20%

        # Add this line to define self.message
        self.message = tk.StringVar()

        # Kết nối database
        try:
            # Tên file database
            db_file = 'DrugDB.db'
            gz_file = db_file + '.gz'

            # Kiểm tra file tồn tại
            if not os.path.exists(db_file) and not os.path.exists(gz_file):
                raise FileNotFoundError(f"Không tìm thấy file '{db_file}' hoặc '{gz_file}'.")

            # Tạo file tạm thời
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
                temp_db_path = temp_db.name

            print("Tạo file tạm thành công:", temp_db_path)

            # Thử xử lý file .gz nếu tồn tại
            if os.path.exists(gz_file):
                print("Phát hiện file nén '.gz'. Giải nén file...")
                with gzip.open(gz_file, 'rb') as gz:
                    with open(temp_db_path, 'wb') as temp_db:
                        temp_db.write(gz.read())
            else:
                print("Sử dụng file SQLite thông thường...")
                # Nếu không phải file nén, xử lý như file SQLite
                with open(db_file, 'rb') as db:
                    with open(temp_db_path, 'wb') as temp_db:
                        temp_db.write(db.read())

            # Kết nối đến file tạm thời
            print("Kết nối tới database tạm thời...")
            self.conn = sqlite3.connect(temp_db_path)
            self.cursor = self.conn.cursor()
            print("Kết nối thành công!")
        except FileNotFoundError as e:
            print(f"Lỗi: {e}")
        except Exception as e:
            print(f"Lỗi không mong muốn: {e}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        self.create_widgets()
        # ... (phần còn lại của __init__)





    def __del__(self):
        """Đóng kết nối database và xóa file tạm thời khi đóng ứng dụng"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'temp_db_path'):
            try:
                os.remove(self.temp_db_path)
            except Exception as e:
                print(f"Lỗi khi xóa file tạm thời: {e}")

    def verify_key(self):
        """Xác nhận key và cập nhật trạng thái"""
        # Check for admin key first
        if self.key_var.get() == "nhatquan" or (socket.gethostname() == "GTSC1D1HAUNH0" and self.key_var.get() == "11"):
            # Create new window for admin functions
            admin_window = tk.Toplevel(self.root)
            admin_app = EncryptDecryptApp(admin_window)
            return

        # Regular key validation
        if self.validate_key():
            self.status_label_var.set("✓ Key hợp lệ")
            self.status_label.configure(foreground="green")
            # Kích hoạt tìm kiếm nếu có dữ liệu
            self.on_search_change()
        else:
            self.status_label_var.set("✗ Key không hợp lệ")
            self.status_label.configure(foreground="red")
            # Xóa kết quả tìm kiếm nếu có
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)

    def validate_percentage(self, P):
        if P == "":
            return True
        try:
            value = float(P)
            return 0 <= value <= 100
        except ValueError:
            return False

    def create_widgets(self):
        style = ttk.Style()
        style.configure("ItalicLabel.TLabel", font=("Arial", 10, "italic"))


        # ------------------ FRAME CHÍNH ------------------
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # ------------------ LEFT FRAME ------------------
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=(0, 20))

        # (row 0) Key, status label, nút kiểm tra
        key_frame = ttk.Frame(left_frame)
        key_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E)
        ttk.Label(key_frame, text="Key:").grid(row=0, column=0, sticky=tk.W)
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=20, show="*")
        self.key_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        self.status_label_var = tk.StringVar()
        self.status_label = ttk.Label(key_frame, textvariable=self.status_label_var)
        self.status_label.grid(row=0, column=2, padx=2, pady=5, sticky=tk.W)

        self.verify_btn = ttk.Button(key_frame, text="Kiểm tra Key", command=self.verify_key)
        self.verify_btn.grid(row=0, column=3, padx=5, pady=5)

        # (row 1) Tên thuốc
        ttk.Label(left_frame, text="Tên thuốc:").grid(row=1, column=0, sticky=tk.W)
        self.brand_var = tk.StringVar()
        self.brand_entry = ttk.Entry(left_frame, textvariable=self.brand_var, width=40)
        self.brand_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.E)

        # (row 2) Hoạt chất
        ttk.Label(left_frame, text="Hoạt chất:").grid(row=2, column=0, sticky=tk.W)
        self.ingredient_var = tk.StringVar()
        self.ingredient_entry = ttk.Entry(left_frame, textvariable=self.ingredient_var, width=40)
        self.ingredient_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.E)

        # (row 5) Tổng toa thuốc
        ttk.Label(left_frame, text="Tổng toa thuốc:").grid(row=5, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.total_med_var = tk.StringVar()
        self.total_med_entry = FormattedEntry(left_frame, textvariable=self.total_med_var, width=15)
        self.total_med_entry.grid(row=5, column=1, padx=(0, 5), pady=5, sticky=tk.W)

        # (row 6) Tổng chi phí YCBT
        ttk.Label(left_frame, text="Tổng chi phí YCBT:").grid(row=6, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.total_var = tk.StringVar()
        self.total_entry = FormattedEntry(left_frame, textvariable=self.total_var, width=15)
        self.total_entry.grid(row=6, column=1, padx=(0, 5), pady=5, sticky=tk.W)

        # (row 7) Hạn mức 1 lần khám
        ttk.Label(left_frame, text="Hạn mức lần khám:").grid(row=7, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.limit_var = tk.StringVar()
        self.limit_entry = FormattedEntry(left_frame, textvariable=self.limit_var, width=15)
        self.limit_entry.grid(row=7, column=1, padx=(0, 5), pady=5, sticky=tk.W)
        
        def swap_ktpvbh_to_total(): #Hàm chuyển giá trị từ ktpvbh_entry sang total_entry
            """Chuyển giá trị từ ktpvbh_entry sang total_entry (giữ format FormattedEntry),
            sau đó xóa giá trị ktpvbh_entry, ktpvbh_vars[] và ktpvbh_var2s[].
            """
            # 1. Lấy nội dung từ ktpvbh_entry
            value_str = self.ktpvbh_entry.get()  

            # 2. Gán sang total_entry
            self.total_entry.delete(0, tk.END)
            self.total_entry.insert(0, value_str)

            # 3. Cho phép sửa ktpvbh_entry (nếu bạn đang đặt state="readonly")
            self.ktpvbh_entry.config(state="normal")
            #    Xóa nội dung trong ktpvbh_entry
            self.ktpvbh_entry.delete(0, tk.END)
            #    Hoặc set về rỗng cho biến StringVar
            self.ktpvbh_var.set("")
            #    Đặt lại thành readonly nếu cần
            self.ktpvbh_entry.config(state="readonly")

            # 4. Xóa giá trị của ktpvbh_vars[] và ktpvbh_var2s[]
            for v in self.ktpvbh_vars:
                v.set("")     # hoặc đặt "0" nếu muốn
            for v2 in self.ktpvbh_var2s:
                v2.set("")    # tương tự

            # 5. Gọi update_ktpvbh_total() để cập nhật lại hiển thị tổng (nếu cần)
            self.update_ktpvbh_total()

            # 6. Cập nhật giá trị của total_entry
            self.update_ktpvbh_total()


        # (row 8) Không thuộc PVBH
        ktpvbh_frame = ttk.Frame(left_frame)
        ktpvbh_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(ktpvbh_frame, text="**Không thuộc PVBH:", style="ItalicLabel.TLabel") \
            .grid(row=0, column=0, padx=(0, 5), sticky=tk.E)

        self.ktpvbh_var = tk.StringVar()
        # Tạo Entry và đặt về trạng thái bình thường
        self.ktpvbh_entry = FormattedEntry(ktpvbh_frame, textvariable=self.ktpvbh_var, width=15)
        self.ktpvbh_entry.config(state="readonly")  # Khóa trạng thái chỉ đọc
        self.ktpvbh_entry.grid(row=0, column=1, sticky=tk.W)

        # Nút SWAP (giả sử bạn đã có hàm swap_ktpvbh_to_total)
        self.swap_icon = tk.PhotoImage(file="swap.png")
        # Thu nhỏ icon nếu cần
        self.swap_icon = self.swap_icon.subsample(25, 25)

        self.swap_btn = ttk.Button(
            ktpvbh_frame,
            image=self.swap_icon,
            command=swap_ktpvbh_to_total
        )
        self.swap_btn.grid(row=0, column=3, padx=(5, 0), sticky=tk.E)

        # 1) Frame để chứa ô nhập số + nút OK trong cột 2
        lines_frame = ttk.Frame(ktpvbh_frame)
        lines_frame.grid(row=0, column=2, sticky=tk.W)

        # 2) Biến lưu giá trị số dòng
        self.num_lines_var = tk.StringVar()

        # 3) Textfield để nhập số dòng
        self.num_lines_var.set("5")
        lines_entry = ttk.Entry(lines_frame, textvariable=self.num_lines_var, width=3)
        lines_entry.pack(side=tk.LEFT, padx=(0, 5))

        # ===== Khởi tạo trước tối đa 5 dòng (hoặc nhiều hơn tùy bạn) =====
        # Danh sách lưu widget của mỗi dòng
        self.ktpvbh_rows = []
        # Nếu bạn cần giữ var1/var2 dạng danh sách, bạn cũng có thể khai báo
        self.ktpvbh_vars = []
        self.ktpvbh_var2s = []

        for i in range(30):
            var1 = tk.StringVar()
            var2 = tk.StringVar()
            
            self.ktpvbh_vars.append(var1)
            self.ktpvbh_var2s.append(var2)

            entry1 = FormattedEntry(ktpvbh_frame, textvariable=var1, width=15)
            entry2 = tk.Entry(ktpvbh_frame, textvariable=var2, width=30)

            # Hàm xóa giá trị cặp var1 & var2 tương ứng
            def clear_vars(v1=var1, v2=var2):
                v1.set("")
                v2.set("")

            btn_delete = ttk.Button(ktpvbh_frame, text="-", width=2, command=clear_vars)

            # Grid chúng vào ngay bây giờ, nhưng ẩn (grid_remove)
            entry1.grid(row=i + 1, column=0, padx=5, pady=2, sticky=tk.W)
            entry2.grid(row=i + 1, column=1, padx=5, pady=2, sticky="ew")
            btn_delete.grid(row=i + 1, column=2, padx=(5, 0), pady=2, sticky=tk.W)

            entry1.grid_remove()
            entry2.grid_remove()
            btn_delete.grid_remove()

            # Gộp vào dict để dễ quản lý (show/hide)
            row_dict = {
                "entry1": entry1,
                "entry2": entry2,
                "btn_delete": btn_delete
            }
            self.ktpvbh_rows.append(row_dict)

            # Ràng buộc sự kiện cập nhật tổng khi var1 thay đổi
            var1.trace_add("write", self.update_ktpvbh_total)


        # Hàm show/hide các dòng theo số dòng nhập
        def show_n_lines():
            try:
                n = int(self.num_lines_var.get())
            except ValueError:
                n = 0

            # Giới hạn 0..5 (nếu bạn chỉ tạo ... dòng)
            if n < 0:
                n = 0
            elif n > 10:
                answer = messagebox.askyesno("ARE YOU SURE", "Hồ sơ có nhiều hơn 10 cái hóa đơn / 10 chi phí không thuộc phạm vi bảo hiểm?\n" "Bạn có chắc muốn tạo nhiều hơn 10 dòng?")
                if answer:
                    answer1 = messagebox.askyesno("ARE YOU SURE", f"Bạn có chắc chắn muốn tạo {n} dòng không đấy?")      
                    if not answer1:
                        # Nếu lần 2 người dùng chọn No => gán n=5
                        n = 5
                        messagebox.showinfo("Thông báo", "Đã tạo 5 dòng")
                        # Sau đó hiển thị 5 dòng và return
                    else:
                        n = int(self.num_lines_var.get())
                        messagebox.showinfo("Thông báo", f"Đã tạo {n} dòng")
                else:        
                    n = 10
                    messagebox.showinfo("Thông báo", "Đã tạo 10 dòng")

            # Ẩn tất cả
            for row_dict in self.ktpvbh_rows:
                row_dict["entry1"].grid_remove()
                row_dict["entry2"].grid_remove()
                row_dict["btn_delete"].grid_remove()

            # Hiển thị n dòng
            for i in range(n):
                row_dict = self.ktpvbh_rows[i]
                row_dict["entry1"].grid()
                row_dict["entry2"].grid()
                row_dict["btn_delete"].grid()


        # 5) Nút OK (nằm cùng lines_frame)
        ok_button = ttk.Button(lines_frame, text="Create Row", command=show_n_lines)
        ok_button.pack(side=tk.LEFT)
        show_n_lines()   # Call show_n_lines() to automatically create initial rows
        # Đảm bảo lưới mở rộng khi thay đổi kích thước
        ktpvbh_frame.columnconfigure(1, weight=1)




        # ------------------ RIGHT FRAME ------------------
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=(5, 15))

        # 4 dòng vitamin/khoáng chất (row 1..4)
        self.drug_entries = {}
        self.drug_labels = {}
        for i in range(4):
            row = i + 1
            drug_name = f"Vitamin / khoáng chất {i+1}:"
            var = tk.StringVar()

            # label sát entry hơn: giảm hoặc bỏ width, giảm padx
            label_var = tk.StringVar(value=drug_name)
            label = ttk.Label(right_frame, textvariable=label_var, anchor='w')
            label.grid(row=row, column=0, padx=(0, 2), pady=5, sticky=tk.W)

            entry = FormattedEntry(right_frame, textvariable=var, width=15)
            entry.grid(row=row, column=1, padx=(0, 5), pady=5, sticky=tk.W)

            delete_btn = ttk.Button(right_frame, text="-", width=2,
                                    command=lambda pos=f"drug{i+1}": self.clear_drug(pos))
            delete_btn.grid(row=row, column=2, padx=5, pady=5)

            self.drug_entries[f"drug{i+1}"] = {"var": var, "entry": entry}
            self.drug_labels[f"drug{i+1}"] = {"var": label_var, "label": label, "is_default": True}

        # Tạo sub-frame cho row 5
        vitamin_frame = ttk.Frame(right_frame)
        vitamin_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=(0, 5), pady=5)
        # Trong sub-frame, sắp xếp theo chiều ngang
        ttk.Label(vitamin_frame, text="Tỉ lệ vitamin:").pack(side=tk.LEFT, padx=(0,5))
        self.discount_var = tk.StringVar(value="20")
        discount_20 = ttk.Radiobutton(vitamin_frame, text="20%", variable=self.discount_var, value="20")
        discount_20.pack(side=tk.LEFT)


        # Row 6: Tạo 1 sub-frame
        coinsurance_frame = ttk.Frame(right_frame)
        coinsurance_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=(0, 5), pady=5)
        # Bên trong sub-frame, pack các widget theo chiều ngang (LEFT)
        ttk.Label(coinsurance_frame, text="Đồng bảo hiểm:").pack(side=tk.LEFT, padx=(0,5))
        self.coinsurance_var = tk.StringVar(value="0")
        self.coinsurance_entry = ttk.Entry(coinsurance_frame, textvariable=self.coinsurance_var, width=5)
        self.coinsurance_entry.pack(side=tk.LEFT, padx=(0,2))
        ttk.Label(coinsurance_frame, text="%").pack(side=tk.LEFT)

        # (row 7) Nút Calculate và Clear All (đều nằm bên trái)
        calculate_btn = ttk.Button(right_frame, text="Calculate/Copy to Clipboard\n\n(PRESS ENTER)", style="Center.TButton", command=self.calculate_total)
        calculate_btn.grid(row=7, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        # BIND sự kiện cho root (hoặc main_frame, right_frame,...)
        self.root.bind("<Return>", lambda event: self.calculate_total())

        clear_btn = ttk.Button(right_frame, text="Clear All", command=self.clear_all_fields)
        clear_btn.grid(row=7, column=1, padx=(5, 5), pady=5, sticky=tk.W)

        # (row 8) Thông báo
        # Label hiển thị thông tin sau khi tính toán
        self.info_label_var = tk.StringVar()
        info_label = ttk.Label(right_frame, textvariable=self.info_label_var, wraplength=500)
        info_label.grid(row=8, column=0, columnspan=4, padx=(0, 5), pady=5, sticky=tk.W)

        bangtinh_btn = ttk.Button(right_frame, text="Mở bảng tính (F1)", command=self.open_excel)
        bangtinh_btn.grid(row=10, column=0, padx=(5, 5), pady=5, sticky=tk.W)
        # Gán phím F1 để gọi hàm open_excel
        self.root.bind("<F1>", lambda event: self.open_excel())

        # ------------------ FRAME KẾT QUẢ ------------------
        result_frame = ttk.Frame(main_frame)
        # Để TreeView full chiều ngang, dùng columnspan=2 + sticky=(W,E,N,S)
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Cấu hình co giãn
        main_frame.grid_rowconfigure(1, weight=1)       # Row 1 trong main_frame co giãn
        main_frame.grid_columnconfigure(0, weight=1)    # Column 0 trong main_frame co giãn
        main_frame.grid_columnconfigure(1, weight=0)    # Column 1 có thể không co giãn
        result_frame.grid_rowconfigure(1, weight=1)     # Bên trong result_frame, row=1 co giãn
        result_frame.grid_columnconfigure(0, weight=1)  # Cho TreeView co giãn

        ttk.Label(result_frame, text="Kết quả tìm kiếm:").grid(row=0, column=0, sticky=tk.W)
        self.result_tree = ttk.Treeview(
            result_frame,
            columns=("reg_no", "drugname", "Phân loại", "ingredient", "reg_no_old", "soQuyetDinh"),
            show="headings",
            height=10
        )
        self.result_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        self.result_tree.heading("reg_no", text="Số đăng ký")
        self.result_tree.heading("drugname", text="Tên thuốc")
        self.result_tree.heading("Phân loại", text="Phân loại")
        self.result_tree.heading("ingredient", text="Hoạt chất")
        self.result_tree.heading("reg_no_old", text="Số đăng ký cũ")
        self.result_tree.heading("soQuyetDinh", text="Số quyết định")
        self.result_tree.column("reg_no", width=80, minwidth=80)
        self.result_tree.column("drugname", width=120, minwidth=150)
        self.result_tree.column("Phân loại", width=70, minwidth=50)
        self.result_tree.column("ingredient", width=200, minwidth=200)
        self.result_tree.column("reg_no_old", width=80, minwidth=80)
        self.result_tree.column("soQuyetDinh", width=120, minwidth=100)

        # ------------------ BINDING & TOOLTIP (nếu có) ------------------
        self.brand_var.trace('w', self.on_search_change)
        self.ingredient_var.trace('w', self.on_search_change)
        self.result_tree.bind('<Double-1>', self.on_tree_double_click)
        self.result_tree.bind("<Enter>", self.on_tree_enter)
        self.result_tree.bind("<Leave>", self.on_tree_leave)
        self.result_tree.bind("<Motion>", self.on_tree_motion)

        # ------------------ COPYRIGHT ------------------
        copyright_label = ttk.Label(
            main_frame,
            text="©Copyright by HauNguyen",
            font=("Arial", 8),
            foreground="grey"
        )
        # Đặt ở hàng “lớn” hơn để nằm cuối
        copyright_label.grid(row=100, column=0, columnspan=2, pady=5, sticky=tk.S)
        main_frame.grid_rowconfigure(100, weight=1)


    def update_ktpvbh_total(self, *args):
        """Cập nhật tổng vào ktpvbh_entry từ 4 ô var1 (bỏ qua var2), loại bỏ khoảng trắng và định dạng số."""
        total = 0
        for var in self.ktpvbh_vars:
            cleaned_value = var.get().replace(" ", "")  # Loại bỏ khoảng trắng
            if cleaned_value.isdigit():  # Kiểm tra nếu là số hợp lệ
                total += int(cleaned_value)

        formatted_total = "{:,}".format(total).replace(",", " ")  # Thay dấu phẩy bằng dấu cách

        # Cho phép cập nhật giá trị vào entry bị disable
        self.ktpvbh_entry.config(state="normal")  # Mở khóa để cập nhật
        self.ktpvbh_var.set(formatted_total)  # Gán tổng đã định dạng vào FormattedEntry
        self.ktpvbh_entry.config(state="readonly")  # Khóa lại sau khi cập nhật



    def get_ktpvbh_values(self):
        selected = []
        for key, var in self.ktpvbh_checkboxes.items():
            if var.get() == 1:
                selected.append(self.ktpvbh_full_names[key])
        return '; '.join(selected)
    
    def confirm_clear(self):
        """Show confirmation dialog before clearing fields"""
        confirm = messagebox.askyesno(
            "Confirm Clear",
            "Are you sure you want to clear all fields?\nThis will reset all values except the KEY.",
            icon='warning'
        )
        if confirm:
            self.clear_all_fields()

    def clear_all_fields(self):
        """Clear all fields except key_var"""
        # Clear brand and ingredient search fields
        self.brand_var.set("")
        self.ingredient_var.set("")

        # Clear all drug entries and reset labels
        for pos in self.drug_entries:
            self.clear_drug(pos)

        # Clear total fields
        self.total_med_var.set("")
        self.total_var.set("")
        self.ktpvbh_var.set("")
        
        # Reset coinsurance to 0
        self.coinsurance_var.set("0")
        
        # Reset discount to default (20%)
        self.discount_var.set("20")

        # Clear info label
        self.info_label_var.set("")
        
        # Clear search results
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        # clear limit_var ---
        self.limit_var.set("")
        # clear tất cả cặp var1/var2 (ktpvbh_vars, ktpvbh_var2s) ---
        for i in range(len(self.ktpvbh_vars)):
            self.ktpvbh_vars[i].set("")
            self.ktpvbh_var2s[i].set("")

        # Reset coinsurance to 0
        self.coinsurance_var.set("0")

        # Reset discount to default (20%)
        self.discount_var.set("20")

        # Clear info label
        self.info_label_var.set("")

        # Clear search results
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)


        # Clear message
        self.message.set("")


    def update_results(self, results: List[Tuple]):
        """Cập nhật kết quả trong Treeview"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        for result in results:
            self.result_tree.insert("", tk.END, values=result)

    def on_tree_enter(self, event):
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry("+0+0")
        self.tooltip.lift()  # Ensure the tooltip is on top
        self.tooltip_label = tk.Label(self.tooltip, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1, wraplength=350)
        self.tooltip_label.pack(ipadx=1)

    def on_tree_leave(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.tooltip_label = None

    def on_tree_motion(self, event):
        try:
            item = self.result_tree.identify_row(event.y)
            if item:
                values = self.result_tree.item(item, 'values')
                if values:
                    ten_thuoc = values[1]
                    hoat_chat_chinh = values[3]
                    phan_loai = values[2]
                    
                    tooltip_text = f"Tên thuốc: {ten_thuoc}\n-----------------------------------------------------------\nHoạt chất: {hoat_chat_chinh}\n-----------------------------------------------------------\nPhân loại: {phan_loai}"
                    
                    if self.tooltip is None:
                        self.tooltip = tk.Toplevel(self.root)
                        self.tooltip.wm_overrideredirect(True)
                        self.tooltip.wm_geometry("+0+0")
                        self.tooltip.lift()  # Ensure the tooltip is on top
                        self.tooltip_label = tk.Label(self.tooltip, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1, wraplength=350)
                        self.tooltip_label.pack(ipadx=1)
                    
                    self.tooltip_label.config(text=tooltip_text)
                    self.tooltip.geometry(f"+{event.x_root}+{event.y_root + 20}")
                    self.tooltip.deiconify()
                else:
                    self.hide_tooltip()
            else:
                self.hide_tooltip()
        except tk.TclError:
            # Handle any Tkinter errors
            self.hide_tooltip()
        except Exception as e:
            # Log any other unexpected errors
            print(f"Unexpected error in on_tree_motion: {e}")
            self.hide_tooltip()

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.withdraw()

    def clear_drug(self, position):
        """Clear the drug label and reset it to the initial state"""
        label_data = self.drug_labels[position]
        entry_data = self.drug_entries[position]
        
        # Reset label to default
        label_data["var"].set(f"Vitamin / khoáng chất {position[-1]}:")
        label_data["is_default"] = True
        
        # Clear price entry
        entry_data["var"].set("")

    def clear_entry(self, var, label_var):
        """Xóa giá trị của một entry field và reset tên thuốc"""
        var.set("")
        # Reset tên thuốc về mặc định
        pos = next(k for k, v in self.drug_entries.items() if v["var"] == var)
        label_var.set(f"Thuốc {pos[-1]}")
        # Đánh dấu label đã về mặc định
        self.drug_labels[pos]["is_default"] = True
    def get_co_insurance_percent(self):
        co_insurance_str = self.coinsurance_var.get().strip()
        return int(co_insurance_str) if co_insurance_str else 0

    def open_excel(self):
        """Giải mã file encrypted.aes, mở file nhưng không cho phép lưu hoặc chỉnh sửa."""
        buffer_size = 64 * 1024
        password = "123456"  # Mật khẩu dùng để giải mã
        encrypted_file = "encrypted.aes"  # File đã mã hóa

        try:
            # Đọc file mã hóa từ ổ cứng vào RAM
            with open(encrypted_file, "rb") as f:
                encrypted_data = f.read()

            # Giải mã vào bộ nhớ RAM
            decrypted_data = io.BytesIO()
            decrypted_data.write(encrypted_data)  # Giả lập file trong RAM
            decrypted_data.seek(0)

            decrypted_output = io.BytesIO()
            pyAesCrypt.decryptStream(decrypted_data, decrypted_output, password, buffer_size)
            decrypted_output.seek(0)

            # Tạo file tạm trong thư mục temp
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, "temp_excel.xlsm")  # Tạo file tạm

            # Ghi dữ liệu giải mã vào file tạm
            with open(temp_file, "wb") as f:
                f.write(decrypted_output.getvalue())

            # **Mở Excel với win32com**
            excel = win32com.client.Dispatch("Excel.Application")
            excel.Visible = True  # Hiển thị Excel
            excel.DisplayAlerts = False  # Không hiển thị cảnh báo

            # **Mở file Excel trong chế độ Read-Only**
            workbook = excel.Workbooks.Open(temp_file, ReadOnly=True)

            # Kiểm tra nếu workbook mở thành công
            if workbook is None:
                raise ValueError("Không thể mở file Excel. Kiểm tra đường dẫn hoặc Excel có lỗi.")

            # **Bảo vệ Workbook để chặn Save As**
            workbook.Protect(Password="readonly", Structure=True, Windows=True)

            # **Bảo vệ tất cả Sheet để ngăn chỉnh sửa**
            for sheet in workbook.Sheets:
                sheet.Protect(Password="readonly", Contents=True, DrawingObjects=True, Scenarios=True)

            workbook.Saved = True  # Ngăn chặn yêu cầu lưu khi đóng file

            print("File Excel đã mở ở chế độ Chỉ đọc và bảo vệ hoàn toàn!")

        except Exception as e:
            print(f"Lỗi khi mở file Excel: {e}")


    def calculate_total(self, *args):
        """
        Hàm tính toán và hiển thị số tiền bảo hiểm chi trả sau khi áp dụng:
        - Hạn mức Vitamin/thuốc bổ (giới hạn 20% tổng toa thuốc).
        - Chi phí không thuộc phạm vi bảo hiểm (ngoai_pvbh).
        - Đồng chi trả (co-insurance).
        - Giới hạn bồi thường (limit).
        """
        import pyperclip

        # Danh sách chứa tên thuốc Vitamin/thuốc bổ được chọn
        vitamins_included = []
        # Danh sách chứa mô tả các khoản chi phí "ngoài phạm vi bảo hiểm"
        excluded_items_list = []  

        # Lặp qua 4 ô nhập cho thuốc
        for i in range(4):
            key = f"drug{i+1}"
            drug_name = self.drug_labels[key]["var"].get()
            drug_value_str = self.drug_entries[key]["var"].get().replace(" ", "")
            
            quantity_var1 = self.ktpvbh_vars[i].get().replace(" ", "")
            excluded_item_description = self.ktpvbh_var2s[i].get().strip()

            # Nếu var1 có dữ liệu dạng số > 0 -> coi là khoản ngoài PVBH => lưu mô tả var2
            if quantity_var1.isdigit() and int(quantity_var1) > 0:
                if excluded_item_description:
                    excluded_items_list.append(excluded_item_description)

            # Nếu giá trị thuốc > 0 và không phải mặc định thì đây là Vitamin/thuốc bổ
            if (drug_value_str.isdigit() 
                and int(drug_value_str) > 0 
                and not self.drug_labels[key]["is_default"]):
                vitamins_included.append(drug_name)

        # Lấy tất cả giá trị từ self.ktpvbh_var2s (bỏ các chuỗi trống / khoảng trắng)
        excluded_items_list = [v2.get().strip() for v2 in self.ktpvbh_var2s if v2.get().strip()]
        # Rồi nối chúng thành 1 chuỗi
        self.ktpvbh_var2 = ", ".join(excluded_items_list) if excluded_items_list else ""

        # Chuẩn bị chuỗi tên Vitamin/thuốc bổ
        vitamins_str = "Vitamin/thuốc bổ"
        if vitamins_included:
            vitamins_str = "Vitamin thuốc bổ: " + ", ".join(vitamins_included)

        try:
            # Lấy các giá trị đầu vào
            total_amount_str = self.total_var.get().replace(' ', '')
            total_med_str = self.total_med_var.get().replace(' ', '')
            ngoai_pvbh_str = self.ktpvbh_var.get().replace(' ', '')
            limit_str = self.limit_var.get().replace(' ', '')

            total_amount = int(total_amount_str) if total_amount_str else 0
            total_med = int(total_med_str) if total_med_str else 0
            ngoai_pvbh = int(ngoai_pvbh_str) if ngoai_pvbh_str else 0
            limit = int(limit_str) if limit_str else 0

            # Nếu total_med = 0 thì gán = total_amount (hoặc ngược lại)
            if total_med == 0 and total_amount > 0:
                total_med = total_amount
            if total_amount == 0 and total_med > 0:
                total_amount = total_med

            # Lấy mức discount cho Vitamin (mặc định 20%)
            discount_percent = int(self.discount_var.get())
            # Lấy tỷ lệ đồng chi trả
            coinsurance_percent = self.get_co_insurance_percent()

            # Tính tổng tiền 4 loại Vitamin
            sum_vitamins_cost = 0
            for entry_data in self.drug_entries.values():
                try:
                    value = int(entry_data["var"].get().replace(' ', ''))
                    sum_vitamins_cost += value
                except ValueError:
                    pass

            # Tính hạn mức Vitamin = 20% tổng toa thuốc
            if discount_percent == 20:
                vit_limit = total_med * 0.2
            else:
                raise ValueError("Invalid discount percentage")

            # Số tiền vượt hạn mức Vitamin
            if sum_vitamins_cost > vit_limit:
                vitamins_over_limit_cost = sum_vitamins_cost - vit_limit
            else:
                vitamins_over_limit_cost = 0

            # Bắt đầu tính tiền BH
            # 1. Trừ phần vượt Vitamin
            payment_before_coinsurance = total_amount - vitamins_over_limit_cost
            # 2. Trừ chi phí ngoài PVBH
            payment_after_ngoai_pvbh = payment_before_coinsurance - ngoai_pvbh
            # 3. So sánh với limit
            #    (nếu có limit > 0, lấy min(...) với limit, còn 0 nghĩa là không giới hạn)
            if limit > 0:
                payment_after_compare = min(payment_after_ngoai_pvbh, limit)
            else:
                payment_after_compare = payment_after_ngoai_pvbh

            # 4. Tính đồng chi trả
            coinsurance_amount = payment_after_compare * (coinsurance_percent / 100)
            final_payment_after_coinsurance = payment_after_compare - coinsurance_amount

            # Chuỗi liệt kê chi phí ngoài PVBH
            excluded_items_str = ", ".join(excluded_items_list) if excluded_items_list else ""

            # ----- BẮT ĐẦU XÂY DỰNG THÔNG ĐIỆP HIỂN THỊ -----
            message = f"Số tiền yêu cầu bồi thường: {total_amount:,.0f}đ.\n"

            # Nếu có vượt hạn mức Vitamin
            if vitamins_over_limit_cost > 0:
                message += (
                    f"Trừ {vitamins_over_limit_cost:,.0f}đ vượt hạn mức 20% "
                    f"tổng toa thuốc ({total_med:,.0f}đ) cho {vitamins_str} "
                    f"({sum_vitamins_cost:,.0f}đ).\n"
                )
            else:
                # Không vượt hạn mức
                if sum_vitamins_cost > 0:
                    message += (
                        "Không vượt hạn mức 20% giá trị tổng toa thuốc "
                        "đối với Vitamin/thuốc bổ.\n"
                    )

            # Nếu có chi phí ngoài PVBH
            if ngoai_pvbh > 0:
                message += (
                    f"Trừ {ngoai_pvbh:,.0f}đ chi phí {excluded_items_str} "
                    "không thuộc phạm vi bảo hiểm.\n"
                )

            # Nếu có limit
            if limit > 0 and payment_after_ngoai_pvbh > limit:
                message += (
                    f"Hạn mức điều trị ngoại trú: {limit:,.0f}đ/ lần khám\n"
                )

            # Hiển thị sau khi đã so sánh limit (trước coinsurance)
            message += f"--> Bồi thường: {payment_after_compare:,.0f}đ"

            # Nếu có đồng chi trả
            if coinsurance_percent > 0:
                message += (
                    f" - đồng bảo hiểm {coinsurance_percent}% "
                    f"= {final_payment_after_coinsurance:,.0f}đ"
                )

            # Gán message vào biến giao diện
            self.message.set(message)
            self.info_label_var.set(message)
            pyperclip.copy(message)

        except ValueError:
            error_msg = "Vui lòng nhập tổng tiền hợp lệ"
            self.info_label_var.set(error_msg)
            self.message.set(error_msg)




    def search_drugs(self, brand_name: str, ingredient_name: str) -> List[Tuple]:
            # Kiểm tra key trước khi tìm kiếm
        if self.status_label_var.get() != "✓ Key hợp lệ":
            return []


        """Tìm kiếm thuốc trong database"""
        query = """
        SELECT [soDangKy], [tenThuoc], [Phân Loại], [hoatChatChinh], [soDangKyCu],  [soQuyetDinh]
        FROM druginformation
        WHERE [tenThuoc] LIKE ? AND [hoatChatChinh] LIKE ?
        LIMIT 10
        """
        def normalize_search_string(search_string):
            return f"%{'%'.join(search_string.split())}%" if search_string else "%"

        brand_pattern = normalize_search_string(brand_name)
        ingredient_pattern = normalize_search_string(ingredient_name)
        
        try:
            self.cursor.execute(query, (brand_pattern, ingredient_pattern))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")
            messagebox.showerror("Database Error", f"An error occurred while searching: {e}")
            return []

    def update_results(self, results: List[Tuple]):
        """Cập nhật kết quả trong Treeview"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        for result in results:
            self.result_tree.insert("", tk.END, values=result)

    def on_search_change(self, *args):
        """Xử lý sự kiện khi người dùng nhập text"""
        # Kiểm tra key trước khi tìm kiếm
        if not self.validate_key():
            return
        """Xử lý sự kiện khi người dùng nhập text"""
        brand_search = self.brand_var.get().strip()
        ingredient_search = self.ingredient_var.get().strip()
        
        if brand_search != self.prev_brand_search or ingredient_search != self.prev_ingredient_search:
            results = self.search_drugs(brand_search, ingredient_search)
            self.update_results(results)
            
            self.prev_brand_search = brand_search
            self.prev_ingredient_search = ingredient_search

    def find_next_available_position(self):
        """Tìm vị trí tiếp theo có thể cập nhật (từ trên xuống)"""
        for i in range(4):
            pos = f"drug{i+1}"
            if self.drug_labels[pos]["is_default"]:
                return pos
        return None

    def on_tree_double_click(self, event):
        """Xử lý sự kiện khi double click vào item trong tree"""
        item = self.result_tree.selection()[0]
        if item:
            values = self.result_tree.item(item)['values']
            if values:
                drug_name = values[1]  # Lấy tên thuốc
                
                # Tìm vị trí tiếp theo có thể cập nhật
                next_pos = self.find_next_available_position()
                if next_pos:
                    self.drug_labels[next_pos]["var"].set(drug_name)
                    self.drug_labels[next_pos]["is_default"] = False

    def __del__(self):
        """Đóng kết nối database khi đóng ứng dụng"""
        if hasattr(self, 'conn'):
            self.conn.close()
class EncryptDecryptApp:
    def __init__(self, master):
        self.master = master
        master.title("Encrypt/Decrypt App")
        master.geometry("400x300")

        self.key = GLOBAL_ENCRYPTION_KEY

        # Get computer name
        full_hostname = socket.gethostname()
        self.hostname = full_hostname

        # Create widgets
        ttk.Label(master, text=f"Computer name: {self.hostname}").pack(pady=10)

        self.input_label = ttk.Label(master, text="Enter text:")
        self.input_label.pack()

        self.input_entry = ttk.Entry(master, width=40)
        self.input_entry.pack()

        self.result_label = ttk.Label(master, text="Result:")
        self.result_label.pack()

        self.result_entry = ttk.Entry(master, width=40, state='readonly')
        self.result_entry.pack()

        self.encrypt_button = ttk.Button(master, text="Encrypt", command=self.encrypt)
        self.encrypt_button.pack(pady=10)

        self.decrypt_button = ttk.Button(master, text="Decrypt", command=self.decrypt)
        self.decrypt_button.pack(pady=10)

    def encrypt(self):
        input_string = self.input_entry.get()
        if input_string:
            encoded_result = encode_string_advanced(input_string, self.key)
            self.result_entry.config(state='normal')
            self.result_entry.delete(0, tk.END)
            self.result_entry.insert(0, encoded_result)
            self.result_entry.config(state='readonly')
        else:
            messagebox.showwarning("Warning", "Please enter text to encrypt.")

    def decrypt(self):
        input_string = self.input_entry.get()
        if input_string:
            try:
                decoded_result = decode_string_advanced(input_string, self.key)
                self.result_entry.config(state='normal')
                self.result_entry.delete(0, tk.END)
                self.result_entry.insert(0, decoded_result)
                self.result_entry.config(state='readonly')
            except:
                messagebox.showerror("Error", "Invalid input for decryption.")
        else:
            messagebox.showwarning("Warning", "Please enter text to decrypt.")

# Add helper functions for encryption/decryption
def xor_encrypt(input_string, key):
    """Perform XOR encryption on the input string using the given key."""
    encrypted_chars = [chr(ord(char) ^ ord(key[i % len(key)])) for i, char in enumerate(input_string)]
    return ''.join(encrypted_chars)

def encode_string_advanced(input_string, key):
    """Encode the input string using XOR encryption and Base64 encoding."""
    xor_encrypted = xor_encrypt(input_string, key)
    byte_string = xor_encrypted.encode('utf-8')
    encoded_bytes = base64.b64encode(byte_string)
    return encoded_bytes.decode('utf-8')

def decode_string_advanced(encoded_string, key):
    """Decode the encoded string using Base64 decoding and XOR decryption."""
    decoded_bytes = base64.b64decode(encoded_string)
    xor_encrypted = decoded_bytes.decode('utf-8')
    return xor_encrypt(xor_encrypted, key)



def main():
    import tkinter as tk  
    root = tk.Tk()
    root.geometry("920x827")
    root.title("Drug Search App")
    app = DrugSearchApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

