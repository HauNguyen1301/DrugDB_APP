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


KEY_TEMP = "17121991"
def get_current_quarter():
    """Lấy quý hiện tại và trả về '1' cho quý 1-2, '2' cho quý 3-4."""
    current_month = datetime.now().month
    quarter = (current_month - 1) // 3 + 1
    return str('1') if quarter <= 2 else str('2')

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
            if user_key == encoded_hostname:
                return True
            return False
        except Exception as e:
            print(f"Error validating key: {e}")
            return False




    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Tra cứu Thuốc - v1.7.1.0")

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
        if self.key_var.get() == "nhatquan":
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
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Frame trái cho tìm kiếm
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=(0, 20))

        # Label và Entry cho key (row 0)
        key_frame = ttk.Frame(left_frame)
        key_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E)

        ttk.Label(key_frame, text="Key:").grid(row=0, column=0, sticky=tk.W)
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=40, show="*")
        self.key_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Thêm nút xác nhận
        self.verify_btn = ttk.Button(key_frame, text="Kiểm tra Key", command=self.verify_key)
        self.verify_btn.grid(row=0, column=2, padx=5, pady=5)

        # Label trạng thái
        self.status_label_var = tk.StringVar()
        self.status_label = ttk.Label(key_frame, textvariable=self.status_label_var)
        self.status_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))


        # Label và Entry cho tên thuốc
        ttk.Label(left_frame, text="Tên thuốc:").grid(row=1, column=0, sticky=tk.W)
        self.brand_var = tk.StringVar()
        self.brand_entry = ttk.Entry(left_frame, textvariable=self.brand_var, width=40)
        self.brand_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Label và Entry cho hoạt chất
        ttk.Label(left_frame, text="Hoạt chất:").grid(row=2, column=0, sticky=tk.W)
        self.ingredient_var = tk.StringVar()
        self.ingredient_entry = ttk.Entry(left_frame, textvariable=self.ingredient_var, width=40)
        self.ingredient_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)



        # Dictionary để lưu trữ các biến và entry fields
        self.drug_entries = {}
        self.drug_labels = {}

        # Frame phải cho các thuốc và tổng tiền
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=(0, 250))  # Thêm padding bên phải

        
        
        # Tạo các trường nhập liệu cho thuốc
        for i in range(4):
            drug_name = f"Vitamin / khoáng chất {i+1}:"
            var = tk.StringVar()
            
            # Create label with StringVar to update text
            label_var = tk.StringVar(value=drug_name)
            label = ttk.Label(right_frame, textvariable=label_var, width=50, anchor='w')
            label.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            
            # Create entry for price input
            entry = FormattedEntry(right_frame, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=5, pady=5)
            
            # Create delete button
            delete_btn = ttk.Button(right_frame, text="-", width=2, 
                                    command=lambda pos=f"drug{i+1}": self.clear_drug(pos))
            delete_btn.grid(row=i, column=2, padx=5, pady=5)
            
            self.drug_entries[f"drug{i+1}"] = {"var": var, "entry": entry}
            self.drug_labels[f"drug{i+1}"] = {"var": label_var, "label": label, "is_default": True}

        # Thêm phần Tỉ lệ ngay sau Thuốc 4, đẩy sang trái
        ttk.Label(right_frame, text="Tỉ lệ vitamin:").grid(row=4, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        
        self.discount_var = tk.StringVar(value="20")
        discount_20 = ttk.Radiobutton(right_frame, text="20%", variable=self.discount_var, value="20")
        discount_20.grid(row=4, column=1, padx=(0, 5), sticky=tk.W)
        

        # discount_50 = ttk.Radiobutton(right_frame, text="50%", variable=self.discount_var, value="50")
        # discount_50.grid(row=4, column=2, padx=(0, 5), sticky=tk.W)
        
        # Tạo một style mới
        style = ttk.Style()
        style.configure("ItalicLabel.TLabel", font=("Arial", 10, "italic"))

        # In your __init__ method or wherever you initialize your variables
        self.ktpvbh_checkboxes = {
            "Thuốc": IntVar(),
            "VTYT": IntVar(),
            "DVKT": IntVar()
        }
        #Add some vertical space
        ttk.Label(left_frame, text="").grid(row=6, column=0, pady=10)
        ttk.Label(left_frame, text="").grid(row=7, column=0, pady=10)
        # Tổng tiền toa thuốc
        ttk.Label(left_frame, text="Tổng toa thuốc:").grid(row=8, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.total_med_var = tk.StringVar()
        self.total_med_entry = FormattedEntry(left_frame, textvariable=self.total_med_var, width=15)
        self.total_med_entry.grid(row=8, column=1, padx=(0, 5), pady=5, sticky=tk.W)
        
        # Tổng tiền YCBT
        ttk.Label(left_frame, text="Tổng chi phí YCBT:").grid(row=9, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.total_var = tk.StringVar()
        self.total_entry = FormattedEntry(left_frame, textvariable=self.total_var, width=15)
        self.total_entry.grid(row=9, column=1, padx=(0, 5), pady=5, sticky=tk.W)


        ktpvbh_frame = ttk.Frame(left_frame)
        ktpvbh_frame.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=5)

        ttk.Label(ktpvbh_frame, text="**Không thuộc PVBH:", style="ItalicLabel.TLabel").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        self.ktpvbh_var = tk.StringVar()
        self.ktpvbh_entry = FormattedEntry(ktpvbh_frame, textvariable=self.ktpvbh_var, width=15)
        self.ktpvbh_entry.grid(row=0, column=1, padx=(0, 5), sticky=tk.W)
        # # KHÔNG THUỘC PVBH
        # ttk.Label(left_frame, text="**Không thuộc PVBH:", style="ItalicLabel.TLabel").grid(row=10, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        # self.ktpvbh_var = tk.StringVar()
        # self.total_entry = FormattedEntry(left_frame, textvariable=self.ktpvbh_var, width=15)
        # self.total_entry.grid(row=10, column=1, padx=(0, 5), pady=5, sticky=tk.W)

        # Add checkboxes
        checkbox_frame = ttk.Frame(ktpvbh_frame)
        checkbox_frame.grid(row=0, column=2, padx=(5, 0), sticky=tk.W)

        ttk.Checkbutton(checkbox_frame, text="Thuốc", variable=self.ktpvbh_checkboxes["Thuốc"]).grid(row=0, column=0, padx=(0, 5))
        ttk.Checkbutton(checkbox_frame, text="VTYT", variable=self.ktpvbh_checkboxes["VTYT"]).grid(row=0, column=1, padx=(0, 5))
        ttk.Checkbutton(checkbox_frame, text="DVKT", variable=self.ktpvbh_checkboxes["DVKT"]).grid(row=0, column=2, padx=(0, 5))

        # Add a method to get the selected values
        




        # Đồng bảo hiểm
        ttk.Label(right_frame, text="Đồng bảo hiểm:").grid(row=7, column=2, padx=(0, 5), pady=5, sticky=tk.W)
        self.coinsurance_var = tk.StringVar(value="0")
        self.coinsurance_entry = ttk.Entry(right_frame, textvariable=self.coinsurance_var, width=5)
        self.coinsurance_entry.grid(row=7, column=3, padx=(0, 5), pady=5, sticky=tk.W)
        ttk.Label(right_frame, text="%").grid(row=7, column=3, padx=(50, 0), pady=5, sticky=tk.W)

        # Thêm xác thực cho trường đồng bảo hiểm
        lenh_xac_thuc = (self.root.register(self.validate_percentage), '%P')
        self.coinsurance_entry.config(validate="key", validatecommand=lenh_xac_thuc)

        # Thêm nút Calculate ( tạo máy tính )
        calculator_btn = ttk.Button(right_frame, text="Open Windows Calculator (F1)", command=lambda: subprocess.run(["calc"]))
        calculator_btn.grid(row=0, column=4, padx=(0, 10), pady=10, sticky=tk.W)

        # Gán phím F1 để mở máy tính Windows
        root.bind("<F1>", lambda event: subprocess.run(["calc"]))


        # Nút Calculate
        calculate_btn = ttk.Button(right_frame, text="Calculate / Copy to Clipboard", command=self.calculate_total)
        calculate_btn.grid(row=9, column=1, padx=(0, 5), pady=5, sticky=tk.W)
        # Add Clear button next to Calculate button
        clear_btn = ttk.Button(right_frame, text="Clear All", command=self.clear_all_fields)
        clear_btn.grid(row=9, column=3, padx=(5, 5), pady=5, sticky=tk.W)

        # Thêm label để hiển thị thông tin sau khi tính toán
        self.info_label_var = tk.StringVar()
        info_label = ttk.Label(right_frame, textvariable=self.info_label_var, wraplength=500)
        info_label.grid(row=10, column=0, columnspan=4, padx=(0, 5), pady=5, sticky=tk.W)



        
        # Khu vực hiển thị kết quả
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(result_frame, text="Kết quả tìm kiếm:").grid(row=0, column=0, sticky=tk.W)
        
        # Treeview để hiển thị kết quả
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=("reg_no", "drugname", "Phân loại", "ingredient",  "reg_no_old",  "soQuyetDinh"),
            show="headings",
            height=10
        )
        self.result_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Định dạng các cột
        self.result_tree.heading("reg_no", text="Số đăng ký")
        self.result_tree.heading("drugname", text="Tên thuốc")
        self.result_tree.heading("Phân loại", text="Phân loại")
        self.result_tree.heading("ingredient", text="Hoạt chất")        
        self.result_tree.heading("reg_no_old", text="Số đăng ký cũ")
        self.result_tree.heading("soQuyetDinh", text="Số quyết định")
        
        # Configure column widths
        self.result_tree.column("reg_no", width=80, minwidth=80)
        self.result_tree.column("drugname", width=120, minwidth=150)
        self.result_tree.column("Phân loại", width=70, minwidth=50)
        self.result_tree.column("ingredient", width=300, minwidth=200)        
        self.result_tree.column("reg_no_old", width=80, minwidth=80)        
        self.result_tree.column("soQuyetDinh", width=120, minwidth=100) 
        
        self.tooltip = None
        self.tooltip_label = None

        # Thanh cuộn
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind events
        self.brand_var.trace('w', self.on_search_change)
        self.ingredient_var.trace('w', self.on_search_change)
        self.result_tree.bind('<Double-1>', self.on_tree_double_click)

        # Add copyright label at the bottom of main_frame
        copyright_label = ttk.Label(main_frame, text="©Copyright by HauNguyen", font=("Arial", 8), foreground="grey")
        copyright_label.grid(row=100, column=0, columnspan=2, pady=5, sticky=tk.S)

        # Make sure the last row (with copyright) expands to fill space
        main_frame.grid_rowconfigure(100, weight=1)
        
        # Add event bindings for tooltip
        self.result_tree.bind("<Enter>", self.on_tree_enter)
        self.result_tree.bind("<Leave>", self.on_tree_leave)
        self.result_tree.bind("<Motion>", self.on_tree_motion)
        
        # Make the result_frame expandable
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
    def get_ktpvbh_values(self):
        selected = []
        for key, var in self.ktpvbh_checkboxes.items():
            if var.get() == 1:
                selected.append(key)
        return ', '.join(selected)
    
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
                    # Assuming 'hoatChatChinh' is the 4th column (index 3) in values
                    hoat_chat_chinh = values[3]
                    
                    tooltip_text = f"Hoạt chất chính: {hoat_chat_chinh}"
                    
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

    def calculate_total(self, *args):
        """Calculate the total and apply the vitamin limit rule"""
        # Danh sách thuốc có giá trị nhập vào
        selected_vitamins = []
        for i in range(4):
            key = f"drug{i+1}"
            drug_name = self.drug_labels[key]["var"].get()  # Lấy tên thuốc từ label
            drug_value = self.drug_entries[key]["var"].get().replace(" ", "")  # Lấy giá trị nhập vào
            ktpvbh_selected = self.get_ktpvbh_values() #Lấy giá trị checkbox

            # Nếu thuốc có số tiền > 0 và không còn là mặc định, thêm vào danh sách
            if drug_value.isdigit() and int(drug_value) > 0 and not self.drug_labels[key]["is_default"]:
                selected_vitamins.append(drug_name)

        # Chuyển danh sách thành chuỗi có dấu phẩy
        # Nếu có thuốc bổ sung, thêm tiền tố "Vitamin thuốc bổ:"
        if selected_vitamins:
            selected_vitamins_str = "Vitamin thuốc bổ: " + ", ".join(selected_vitamins)
        else:
            selected_vitamins_str = "Vitamin/thuốc bổ"


        try:
            # Get the total_amount (tổng số tiền YCBT)
            total_amount_str = self.total_var.get().replace(' ', '')
            total_amount = int(total_amount_str) if total_amount_str else 0

            # Get the total_med (tổng toa thuốc)
            total_med_str = self.total_med_var.get().replace(' ', '')
            total_med = int(total_med_str) if total_med_str else 0

            ngoai_pvbh_str = self.ktpvbh_var.get().replace(' ', '')
            ngoai_pvbh = int(ngoai_pvbh_str) if ngoai_pvbh_str else 0

            # If total_med is not provided, use total_amount as total_med
            if total_med == 0 and total_amount > 0:
                total_med = total_amount
            if total_amount == 0 and total_med >0:
                total_amount = total_med

            # Get the selected discount percentage
            discount_percent = int(self.discount_var.get())
            # Get the co-insurance percentage
            co_insurance_percent = self.get_co_insurance_percent()
            # Calculate the sum of the 4 drug prices
            sum_drugs = 0
            for entry_data in self.drug_entries.values():
                try:
                    # Convert formatted price to number
                    value = int(entry_data["var"].get().replace(' ', ''))
                    sum_drugs += value
                except ValueError:
                    # If the entry is not a valid number, skip it
                    pass
            
            # Calculate the vitamin limit
            if discount_percent == 20:
                vit_limit = total_med * 0.2
            else:
                raise ValueError("Invalid discount percentage")
            
            #result là chi phí vitamin vượt hạn mức
            # Calculate the result (amount exceeding the limit)
            if sum_drugs > vit_limit:
                result = sum_drugs - vit_limit
            else:
                result = 0
                

             # Update the info label
            # if result > 0 or co_insurance_percent > 0:
            #     message = f"Số tiền Yêu cầu: {total_amount:,.0f}đ.\n"
            #     if result > 0:
            #         message += f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc ({total_med:,.0f}đ) đối với Vitamin/thuốc bổ ({sum_drugs:,.0f}đ).\n"
            #     message += f"--> Thanh toán: {payment_before_co_insurance:,.0f}đ"
            #     if co_insurance_percent > 0:
            #         message += f" - đồng bảo hiểm {co_insurance_percent}% = {final_payment:,.0f}đ"
            #     self.message.set(message)
            #     self.info_label_var.set(self.message.get())
            #     pyperclip.copy(self.message.get())  # Copy to clipboard
            # else:
            #     self.message.set("Không vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.")
            #     self.info_label_var.set(self.message.get())  
            # Calculate the payment after deducting the excess amount
            payment_before_co_insurance = total_amount - result
            #1450.000 = 1450.000 - 0
            payment_after_ngoai_pvbh = payment_before_co_insurance - ngoai_pvbh  
            #700.000 = 1450.000 - 750.000
            # Apply co-insurance
            co_insurance_amount = payment_after_ngoai_pvbh * ( co_insurance_percent / 100)
            #      140k           = 700k * (20/100)
            final_payment = payment_before_co_insurance - co_insurance_amount
            #      560k           = 700k - 140k
           
            if ngoai_pvbh <= 0:
                if result > 0 or co_insurance_percent > 0:
                    message = f"Số tiền yêu cầu: {total_amount:,.0f}đ.\n"
                    if result > 0:
                        # message += f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc ({total_med:,.0f}đ) đối với Vitamin/thuốc bổ ({sum_drugs:,.0f}đ).\n"
                        message += f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc ({total_med:,.0f}đ) đối với {selected_vitamins_str} ({sum_drugs:,.0f}đ).\n"
                    message += f"--> Thanh toán: {payment_before_co_insurance:,.0f}đ"
                    if co_insurance_percent > 0:
                        message += f" - đồng bảo hiểm {co_insurance_percent}% = {final_payment:,.0f}đ"
                    self.message.set(message)
                    self.info_label_var.set(self.message.get())
                    pyperclip.copy(self.message.get())  # Copy to clipboard
                else:
                    self.message.set("Không vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.\n")
                    self.info_label_var.set(self.message.get())
            else:
                if result > 0 or co_insurance_percent > 0:
                    
                    payment_after_co_insurance_and_ngoai_pvbh = payment_after_ngoai_pvbh - co_insurance_amount
                    message = f"Số tiền Yêu cầu: {total_amount:,.0f}đ.\n"
                    if result > 0:
                        # message += f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc ({total_med:,.0f}đ) đối với Vitamin/thuốc bổ ({sum_drugs:,.0f}đ).\n"                        
                        # Cập nhật thông báo
                        message += f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc ({total_med:,.0f}đ) đối với {selected_vitamins_str} ({sum_drugs:,.0f}đ).\n"

                    message += f"Trừ {ngoai_pvbh:,.0f}đ chi phí {ktpvbh_selected} không thuộc phạm vi bảo hiểm.\n"
                    message += f"--> Thanh toán: {payment_after_ngoai_pvbh:,.0f}đ"
                    if co_insurance_percent > 0:
                        message += f" - đồng bảo hiểm {co_insurance_percent}% = {payment_after_co_insurance_and_ngoai_pvbh:,.0f}đ"
                    self.message.set(message)
                    self.info_label_var.set(self.message.get())
                    pyperclip.copy(self.message.get())  # Copy to clipboard
                else:
                    message = f"Trừ {ngoai_pvbh:,.0f}đ chi phí {ktpvbh_selected} không thuộc phạm vi bảo hiểm.\n--> Thanh toán {payment_after_ngoai_pvbh:,.0f}đ"
                    self.message.set(message)
                    self.info_label_var.set(self.message.get())
                    pyperclip.copy(self.message.get())  # Copy to clipboard


        except ValueError:
            self.info_label_var.set("Vui lòng nhập tổng tiền hợp lệ")
            self.message.set("Vui lòng nhập tổng tiền hợp lệ")


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
if __name__ == "__main__":
    root = tk.Tk()
    app = DrugSearchApp(root)
    root.mainloop()


# Update 0.3.1
# •	Remove 50%
# •	Fix money input error
# •	Adjust display information (max 20 lines, replace old registration number, expiration date)
# Update 0.5.1
# •	Update new admin function
# •	Change UI/UX
# •	Add copay
# Update 1.5.1
# •	Release alpha version
# •	Store key in a file
# •	Search for drugs by drug name and ingredient name
# •	Store search results in Treeview
# •	Add double-click function on items in Treeview to input drug name
# Update 1.5.2
# •	Add non-insurance-covered costs
# Update 1.5.3
# •	Allow copy-pasting in money fields
# •	Fix copy-to-clipboard issue in some cases
# •	Correct spelling display
# •	Add "Clear All" button
# Update 1.6.1
# •	Add a new category for drugs (Vitamins, Minerals)
# •	Adjust display information after calculation
# Update 1.6.2
# •	Fix database file type issue, no need to enable file name extension
# Update 1.6.3
# •	Downgrade to Python 3.8.0
# Update 1.6.4
# •	Change table view
# •	Improve search
# •	Fix database not automatically deleting after extraction
# Update 1.7.0
# •	Change Global Key function
# •	Update to add vitamin_name to output string
# •	Add calculator 
# Update 1.7.0.1
# •	Fix Copay tính sai
# Update 1.7.1.0
# •	Change key encryption function (change per 2 quarters)
# •	Add check box for non-insurance-covered costs