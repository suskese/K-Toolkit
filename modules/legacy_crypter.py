module_version = "1.0.0"
module_name = "Legacy Crypter"
module_emoji = "🔒"
module_icon = "icon.png"
module_description = "A legacy file encryption/decryption module using AES."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 6,
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "default_key_length": {
        "type": "int",
        "default": 32,
        "desc": "Default key length (bytes)"
    }
}

# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = None  # Set to your UI class if exists

import os
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import customtkinter as ctk
from tkinter import filedialog

class LegacyCrypterUI(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.title = module_name
        self.description = module_description
        self.version = module_version
        self.selected_file = None
        self.mode = "encrypt"
        self.key_var = ctk.StringVar()
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=8)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text="Legacy Crypter", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        ctk.CTkButton(frame, text="Select File", command=self.select_file).grid(row=1, column=0, pady=5)
        self.selected_file_label = ctk.CTkLabel(frame, text="No file selected", font=ctk.CTkFont(size=13))
        self.selected_file_label.grid(row=2, column=0, pady=5)
        ctk.CTkLabel(frame, text="Mode:").grid(row=3, column=0, pady=(10,0))
        self.mode_var = ctk.StringVar(value="encrypt")
        mode_menu = ctk.CTkOptionMenu(frame, variable=self.mode_var, values=["encrypt", "decrypt"])
        mode_menu.grid(row=4, column=0, pady=5)
        ctk.CTkLabel(frame, text="Key:").grid(row=5, column=0, pady=(10,0))
        ctk.CTkEntry(frame, textvariable=self.key_var, show="*").grid(row=6, column=0, pady=5)
        ctk.CTkButton(frame, text="Process", command=self.crypt_action).grid(row=7, column=0, pady=(10, 20))
        self.status_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=8, column=0, pady=5)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select a File", filetypes=(("All files", "*.*"),))
        if file_path:
            self.selected_file = file_path
            self.selected_file_label.configure(text=os.path.basename(file_path))
        else:
            self.selected_file = None
            self.selected_file_label.configure(text="No file selected")

    def crypt_action(self):
        self.mode = self.mode_var.get()
        key = self.key_var.get()
        if not self.selected_file:
            self.status_label.configure(text="No file selected.")
            return
        if not key:
            self.status_label.configure(text="No key provided.")
            return
        try:
            with open(self.selected_file, "r" if self.mode == "encrypt" else "rb") as f:
                data = f.read()
            if self.mode == "encrypt":
                encrypted = LegacyCrypterLogic.encrypt(data, key)
                out_path = self.selected_file + ".enc"
                with open(out_path, "w") as f:
                    f.write(encrypted)
                self.status_label.configure(text=f"Encrypted: {os.path.basename(out_path)}")
            else:
                decrypted = LegacyCrypterLogic.decrypt(data, key)
                out_path = self.selected_file.replace(".enc", ".dec")
                with open(out_path, "w") as f:
                    f.write(decrypted)
                self.status_label.configure(text=f"Decrypted: {os.path.basename(out_path)}")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")

class LegacyCrypterLogic:
    @staticmethod
    def encrypt(data, key):
        cipher = AES.new(LegacyCrypterLogic._get_key(key), AES.MODE_CBC)
        encrypted_data = cipher.encrypt(pad(data.encode(), AES.block_size))
        return base64.b64encode(cipher.iv + encrypted_data).decode()

    @staticmethod
    def decrypt(encrypted_data, key):
        raw_data = base64.b64decode(encrypted_data)
        iv = raw_data[:AES.block_size]
        cipher = AES.new(LegacyCrypterLogic._get_key(key), AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(raw_data[AES.block_size:]), AES.block_size).decode()

    @staticmethod
    def _get_key(key):
        # Ensure the key is 16 bytes (AES-128)
        return key.encode().ljust(16, b'0')[:16]

def home_widget(parent):
    frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
    ctk.CTkLabel(frame, text="Legacy Crypter Quick Info", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
    ctk.CTkLabel(frame, text="Encrypt/decrypt files using AES.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
    return frame
