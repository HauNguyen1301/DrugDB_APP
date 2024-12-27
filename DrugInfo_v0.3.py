import tkinter as tk
from tkinter import ttk
import sqlite3
from typing import List, Tuple


class FormattedEntry(ttk.Entry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.variable = kwargs.get('textvariable') or tk.StringVar()
        self.variable.trace('w', self.format_number)
        self.configure(textvariable=self.variable)
        self.configure(validate="key")
        self.configure(validatecommand=(self.register(self.validate_numeric), '%P'))

    def format_number(self, *args):
        value = self.variable.get().replace(' ', '')  # Remove existing spaces
        if value.isdigit():
            formatted = ' '.join([value[max(i-3, 0):i] for i in range(len(value), 0, -3)][::-1])
            self.variable.set(formatted)

    def validate_numeric(self, text):
        return text == "" or text.replace(' ', '').isdigit()

class DrugSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Tra cứu Thuốc")
        
        # Kết nối database
        self.conn = sqlite3.connect('drugDB.sqlite')
        self.cursor = self.conn.cursor()
        
        # Biến để lưu trữ giá trị tìm kiếm trước đó
        self.prev_brand_search = ""
        self.prev_ingredient_search = ""
        
        # Tạo giao diện
        self.create_widgets()


    def create_widgets(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Frame trái cho tìm kiếm
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 20))

        # Label và Entry cho tên thuốc
        ttk.Label(left_frame, text="Tên thuốc:").grid(row=0, column=0, sticky=tk.W)
        self.brand_var = tk.StringVar()
        self.brand_entry = ttk.Entry(left_frame, textvariable=self.brand_var, width=40)
        self.brand_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Label và Entry cho hoạt chất
        ttk.Label(left_frame, text="Hoạt chất:").grid(row=1, column=0, sticky=tk.W)
        self.ingredient_var = tk.StringVar()
        self.ingredient_entry = ttk.Entry(left_frame, textvariable=self.ingredient_var, width=40)
        self.ingredient_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # Frame phải cho các thuốc và tổng tiền
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.N))

        # Dictionary để lưu trữ các biến và entry fields
        self.drug_entries = {}
        self.drug_labels = {}
        
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



        # Tổng tiền
        ttk.Label(right_frame, text="Tổng tiền:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.total_var = tk.StringVar()
        total_entry = FormattedEntry(right_frame, textvariable=self.total_var, width=15)
        total_entry.grid(row=4, column=1, padx=5, pady=5)

        # Nút Calculate
        calculate_btn = ttk.Button(right_frame, text="Calculate", command=self.calculate_total)
        calculate_btn.grid(row=4, column=2, padx=5, pady=5)

        # New label below the total price
        self.info_label_var = tk.StringVar()
        info_label = ttk.Label(right_frame, textvariable=self.info_label_var)
        info_label.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        
        # Khu vực hiển thị kết quả
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        ttk.Label(result_frame, text="Kết quả tìm kiếm:").grid(row=0, column=0, sticky=tk.W)
        
        # Treeview để hiển thị kết quả
        self.result_tree = ttk.Treeview(
            result_frame, 
            columns=("reg_no", "brand", "ingredient", "company", "country","new_column"), 
            show="headings",
            height=20
        )
        self.result_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Định dạng các cột
        self.result_tree.heading("reg_no", text="Số đăng ký")
        self.result_tree.heading("brand", text="Tên thuốc")
        self.result_tree.heading("ingredient", text="Hoạt chất")
        self.result_tree.heading("company", text="Công ty sản xuất")
        self.result_tree.heading("country", text="Quốc gia")
        self.result_tree.heading("new_column", text="Hàm lượng")
        
    # Configure column widths
        self.result_tree.column("reg_no", width=100, minwidth=100)
        self.result_tree.column("brand", width=200, minwidth=150)
        self.result_tree.column("ingredient", width=400, minwidth=200)
        self.result_tree.column("company", width=150, minwidth=100)
        self.result_tree.column("country", width=100, minwidth=80)
        self.result_tree.column("new_column", width=250, minwidth=200) 
        
        # Thanh cuộn
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind events
        self.brand_var.trace('w', self.on_search_change)
        self.ingredient_var.trace('w', self.on_search_change)
        self.result_tree.bind('<Double-1>', self.on_tree_double_click)

        # Add copyright label at the bottom of main_frame
        copyright_label = ttk.Label(main_frame, text="© Copyright by Hau   -   version 1.0", font=("Arial", 8), foreground="grey")
        copyright_label.grid(row=100, column=0, columnspan=2, pady=5, sticky=tk.S)

        # Make sure the last row (with copyright) expands to fill space
        main_frame.grid_rowconfigure(100, weight=1)

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

    def calculate_total(self):
        """Calculate the total and apply the vitamin limit rule"""
        try:
            # Convert formatted total to number
            total_amount = int(self.total_var.get().replace(' ', ''))
            
            # Calculate 20% of the total for vitamins
            vit = total_amount * 0.2
            
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
            
            # Calculate the result
            result = sum_drugs - vit
            
            # Update the info label
            if result > 0:
                self.info_label_var.set(f"Trừ {result:,.0f}đ số tiền vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ")
            else:
                self.info_label_var.set("Không vượt hạn mức 20% giá trị tổng toa thuốc đối với Vitamin/thuốc bổ")
        
        except ValueError:
            # Handle the case where the total amount is not a valid number
            self.info_label_var.set("Vui lòng nhập tổng tiền hợp lệ")

    def search_drugs(self, brand_name: str, ingredient_name: str) -> List[Tuple]:
        """Tìm kiếm thuốc trong database"""
        query = """
        SELECT [Registration_number], [MedicineName], [Ingredient], [Manufacturer], [Manufacturing_country],[Ingredient]
        FROM druginfo
        WHERE [MedicineName] LIKE ? AND [Ingredient] LIKE ?
        """
        brand_pattern = f"%{brand_name}%" if brand_name else "%"
        ingredient_pattern = f"%{ingredient_name}%" if ingredient_name else "%"
        
        self.cursor.execute(query, (brand_pattern, ingredient_pattern))
        return self.cursor.fetchall()

    def update_results(self, results: List[Tuple]):
        """Cập nhật kết quả trong Treeview"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        for result in results:
            self.result_tree.insert("", tk.END, values=result)

    def on_search_change(self, *args):
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