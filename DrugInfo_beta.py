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


class FormattedEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            hostname = socket.gethostname()[7:]
            
            # Use a fixed key for encryption (you can change this to a more secure key)
            encryption_key = "13011991"
            
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
        self.root.title("Ứng dụng Tra cứu Thuốc - beta 0.3.1")

        # Initialize previous search variables
        self.prev_brand_search = ""
        self.prev_ingredient_search = ""
        self.discount_var = tk.StringVar(value="20")  # Default to 20%

        # Add this line to define self.message
        self.message = tk.StringVar()
        # Kết nối database
        try:
            # Tạo một file tạm thời
            with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
                temp_db_path = temp_db.name
            
            # Giải nén và ghi nội dung vào file tạm thời
            with gzip.open('DrugDB.db.gz', 'rb') as gz_file:
                with open(temp_db_path, 'wb') as temp_db:
                    temp_db.write(gz_file.read())
            
            # Kết nối đến file tạm thời
            self.conn = sqlite3.connect(temp_db_path)
            self.cursor = self.conn.cursor()
            
            # Lưu đường dẫn file tạm thời để xóa sau này
            self.temp_db_path = temp_db_path
            
            print("Kết nối cơ sở dữ liệu thành công")
        except Exception as e:
            print(f"Lỗi khi kết nối cơ sở dữ liệu: {e}")
            # Có thể thêm xử lý lỗi ở đây, ví dụ: hiển thị thông báo lỗi cho người dùng

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


    def create_widgets(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Frame trái cho tìm kiếm
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))

        # Label và Entry cho key (row 0)
        key_frame = ttk.Frame(left_frame)
        key_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E)

        ttk.Label(key_frame, text="Key:").grid(row=0, column=0, sticky=tk.W)
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=40)
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
            drug_name = f"Thuốc {i+1}"
            var = tk.StringVar()
            
            # Create label with StringVar to update text
            label_var = tk.StringVar(value=drug_name)
            label = ttk.Label(right_frame, textvariable=label_var)
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
        ttk.Label(right_frame, text="Tỉ lệ:").grid(row=4, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        
        self.discount_var = tk.StringVar(value="20")
        discount_20 = ttk.Radiobutton(right_frame, text="20%", variable=self.discount_var, value="20")
        discount_20.grid(row=4, column=1, padx=(0, 5), sticky=tk.W)
        
        # discount_50 = ttk.Radiobutton(right_frame, text="50%", variable=self.discount_var, value="50")
        # discount_50.grid(row=4, column=2, padx=(0, 5), sticky=tk.W)

        # Tổng tiền
        ttk.Label(right_frame, text="Tổng tiền:").grid(row=5, column=0, padx=(0, 5), pady=5, sticky=tk.W)
        self.total_var = tk.StringVar()
        total_entry = FormattedEntry(right_frame, textvariable=self.total_var, width=15)
        total_entry.grid(row=5, column=1, padx=(0, 5), pady=5, sticky=tk.W)

        # Nút Calculate
        calculate_btn = ttk.Button(right_frame, text="Calculate / Copy to Clipboard", command=self.calculate_total)
        calculate_btn.grid(row=5, column=2, padx=(0, 5), pady=5, sticky=tk.W)

        # Thêm label để hiển thị thông tin sau khi tính toán
        self.info_label_var = tk.StringVar()
        info_label = ttk.Label(right_frame, textvariable=self.info_label_var, wraplength=400)
        info_label.grid(row=6, column=0, columnspan=3, padx=(0, 5), pady=5, sticky=tk.W)

        
        # Khu vực hiển thị kết quả
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        ttk.Label(result_frame, text="Kết quả tìm kiếm:").grid(row=0, column=0, sticky=tk.W)
        
        # Treeview để hiển thị kết quả
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=("reg_no", "brand", "ingredient", "reg_no_old", "ngayHetHan", "soQuyetDinh"),
            show="headings",
            height=20
        )
        self.result_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Định dạng các cột
        self.result_tree.heading("reg_no", text="Số đăng ký")
        self.result_tree.heading("brand", text="Tên thuốc")
        self.result_tree.heading("ingredient", text="Hoạt chất")
        self.result_tree.heading("reg_no_old", text="Số đăng ký cũ")
        self.result_tree.heading("ngayHetHan", text="Ngày hết hạn")
        self.result_tree.heading("soQuyetDinh", text="Số quyết định")
        
        # Configure column widths
        self.result_tree.column("reg_no", width=100, minwidth=100)
        self.result_tree.column("brand", width=200, minwidth=150)
        self.result_tree.column("ingredient", width=450, minwidth=200)
        self.result_tree.column("reg_no_old", width=100, minwidth=100)
        self.result_tree.column("ngayHetHan", width=100, minwidth=50)
        self.result_tree.column("soQuyetDinh", width=150, minwidth=100) 
        
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
        copyright_label = ttk.Label(main_frame, text="©Copyright by Hau   -   version 0.3.1", font=("Arial", 8), foreground="grey")
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
                    # Assuming 'hoatChatChinh' is the 3rd column (index 2) in values
                    hoat_chat_chinh = values[2]
                    
                    tooltip_text = f"Hoạt chất chính: {hoat_chat_chinh}"
                    
                    self.tooltip_label.config(text=tooltip_text)
                    self.tooltip.geometry(f"+{event.x_root}+{event.y_root + 20}")
                    self.tooltip.deiconify()
            else:
                self.tooltip.withdraw()
        except tk.TclError:
            pass

    def clear_drug(self, position):
        """Clear the drug label and reset it to the initial state"""
        label_data = self.drug_labels[position]
        entry_data = self.drug_entries[position]
        
        # Reset label to default
        label_data["var"].set(f"Thuốc {position[-1]}")
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

    def calculate_total(self, *args):
        """Calculate the total and apply the vitamin limit rule"""

        try:
            # Convert formatted total to number
            total_amount = int(self.total_var.get().replace(' ', ''))
            
            # Get the selected discount percentage
            discount_percent = int(self.discount_var.get())

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
                vit_limit = total_amount * 0.2
            # elif discount_percent == 50:
            #     vit_limit = total_amount * 0.5
            else:
                raise ValueError("Invalid discount percentage")
            
            # Calculate the result (amount exceeding the limit)
            if sum_drugs > vit_limit:
                result = sum_drugs - vit_limit
            else:
                result = 0
            
            # Update the info label
            if result > 0:
                if discount_percent == 20:
                    self.message.set(f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.")
                # elif discount_percent == 50:
                #     self.message.set(f"Trừ {result:,.0f}đ số tiền vượt hạn mức 50% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.")
                self.info_label_var.set(self.message.get())
                pyperclip.copy(self.message.get())  # Copy to clipboard
            else:
                if discount_percent == 20:
                    self.message.set("Không vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.")
                # elif discount_percent == 50:
                #     self.message.set("Không vượt hạn mức 50% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ.")
                self.info_label_var.set(self.message.get())
        
        except ValueError:
            # Handle the case where the total amount is not a valid number
            self.info_label_var.set("Vui lòng nhập tổng tiền hợp lệ")
            self.message.set("Vui lòng nhập tổng tiền hợp lệ")

    def search_drugs(self, brand_name: str, ingredient_name: str) -> List[Tuple]:
            # Kiểm tra key trước khi tìm kiếm
        if self.status_label_var.get() != "✓ Key hợp lệ":
            return []


        """Tìm kiếm thuốc trong database"""
        query = """
        SELECT [soDangKy], [tenThuoc], [hoatChatChinh], [soDangKyCu], [ngayHetHan], [soQuyetDinh]
        FROM druginformation
        WHERE [tenThuoc] LIKE ? AND [hoatChatChinh] LIKE ?
        LIMIT 20
        """
        brand_pattern = f"%{brand_name}%" if brand_name else "%"
        ingredient_pattern = f"%{ingredient_name}%" if ingredient_name else "%"
        
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DrugSearchApp(root)
    root.mainloop()