import base64
import socket
import tkinter as tk
from tkinter import ttk, messagebox

def xor_encrypt(input_string, key):
    encrypted_chars = [chr(ord(char) ^ ord(key[i % len(key)])) for i, char in enumerate(input_string)]
    return ''.join(encrypted_chars)

def encode_string_advanced(input_string, key):
    xor_encrypted = xor_encrypt(input_string, key)
    byte_string = xor_encrypted.encode('utf-8')
    encoded_bytes = base64.b64encode(byte_string)
    encoded_string = encoded_bytes.decode('utf-8')
    return encoded_string

def decode_string_advanced(encoded_string, key):
    decoded_bytes = base64.b64decode(encoded_string)
    xor_encrypted = decoded_bytes.decode('utf-8')
    original_string = xor_encrypt(xor_encrypted, key)
    return original_string

class EncryptDecryptApp:
    def __init__(self, master):
        self.master = master
        master.title("Encrypt/Decrypt App")
        master.geometry("400x300")

        self.key = '130119910109199117122021'

        # Get computer name
        full_hostname = socket.gethostname()
        if full_hostname[:4].upper() == "GTSC":
            self.hostname = full_hostname[7:]
        else:
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

root = tk.Tk()
app = EncryptDecryptApp(root)
root.mainloop()

#eXJlf3kJ - my key
#fXx+dn14CQ== - Anh Long key
#f3R4eHB1bQE= - Nghĩa key

