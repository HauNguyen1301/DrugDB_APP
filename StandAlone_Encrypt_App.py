import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

# Global encryption key
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

def process_excel_file(input_file, output_file):
    """Process the Excel file, encrypt values in column A and save to column B."""
    try:
        # Read the Excel file
        df = pd.read_excel(input_file, header=None)

        # Ensure column A exists
        if df.empty or df.iloc[:, 0].isnull().all():
            raise ValueError("Column A is empty or missing.")

        # Encrypt values from column A and save in column B
        df['B'] = df[0].apply(lambda x: encode_string_advanced(str(x), GLOBAL_ENCRYPTION_KEY) if pd.notnull(x) else None)

        # Save the updated DataFrame to a new Excel file
        df.to_excel(output_file, index=False, header=False)
        messagebox.showinfo("Success", f"File processed successfully! Encrypted values saved to {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def select_input_file():
    """Open a file dialog to select the input file."""
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    return file_path

def select_output_file():
    """Open a file dialog to select the output file location."""
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
    return file_path

def main():
    """Main function to create the GUI."""
    root = tk.Tk()
    root.title("Excel Encrypt/Decrypt Tool")

    # Input file selection
    tk.Label(root, text="Select Input File:").pack(pady=5)
    input_button = tk.Button(root, text="Browse Input File", command=lambda: input_var.set(select_input_file()))
    input_button.pack()
    input_var = tk.StringVar()
    input_entry = tk.Entry(root, textvariable=input_var, width=50)
    input_entry.pack(pady=5)

    # Output file selection
    tk.Label(root, text="Select Output File:").pack(pady=5)
    output_button = tk.Button(root, text="Browse Output File", command=lambda: output_var.set(select_output_file()))
    output_button.pack()
    output_var = tk.StringVar()
    output_entry = tk.Entry(root, textvariable=output_var, width=50)
    output_entry.pack(pady=5)

    # Process file button
    process_button = tk.Button(root, text="Process File", command=lambda: process_excel_file(input_var.get(), output_var.get()))
    process_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()