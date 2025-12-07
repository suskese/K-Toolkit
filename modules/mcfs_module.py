import argparse
import os
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import sys
import customtkinter as ctk
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import subprocess
import tempfile
import threading
from PIL import Image
import cv2

# Try to import RSCodec from reedsolo, set to None if not available
try:
    from reedsolo import RSCodec
except ImportError:
    RSCodec = None

# --- Module Metadata ---
module_name = "MCFS"
module_icon = "icon.png"
module_emoji = "     🗂️"
module_version = "1.0.0"
module_description = "Encrypt, decrypt, and view MCFS files with optional password and recovery."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 2,
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "default_recovery_percent": {
        "type": "int",
        "default": 10,
        "desc": "Default recovery percent for new encryptions"
    }
}
# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = None  # Set to your UI class if exists

def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        # Use a default key if no password is provided (not secure, but allows optional password)
        password = 'default_mcfs_password'
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())
    return kdf.derive(password.encode())

def encrypt_file(input_path, output_path, password, recovery_percent):
    salt = secrets.token_bytes(16)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)
    with open(input_path, 'rb') as f:
        data = f.read()
    if RSCodec and recovery_percent > 0:
        nsym = max(1, int(len(data) * recovery_percent // 100))
        rs = RSCodec(nsym)
        data = rs.encode(data)
    ct = aesgcm.encrypt(nonce, data, None)
    with open(output_path, 'wb') as f:
        f.write(b'MCFS')
        f.write(salt)
        f.write(nonce)
        f.write(ct)
    print(f"Encrypted to {output_path}")

def decrypt_file(input_path, output_path, password, view_only=False):
    with open(input_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'MCFS':
            print("Not a valid .mcfs file")
            sys.exit(1)
        salt = f.read(16)
        nonce = f.read(12)
        ct = f.read()
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    try:
        data = aesgcm.decrypt(nonce, ct, None)
    except Exception as e:
        print("Decryption failed:", e)
        sys.exit(1)
    if RSCodec:
        try:
            for nsym in range(1, 256):
                try:
                    rs = RSCodec(nsym)
                    data = rs.decode(data)[0]
                    break
                except Exception:
                    continue
        except Exception:
            pass
    if view_only:
        try:
            print(data.decode('utf-8'))
        except Exception:
            print("[Non-text file or decode error]")
        return
    with open(output_path, 'wb') as f:
        f.write(data)
    print(f"Decrypted to {output_path}")

class MCFSModuleUI(ctk.CTkFrame):
    def __init__(self, parent, settings=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.file_path = ctk.StringVar()
        self.password = ctk.StringVar()
        self.recovery = ctk.IntVar(value=0)
        self.mode = ctk.StringVar(value="encrypt")
        self.output_dir = ctk.StringVar()

        # Left: Viewer
        self.viewer_frame = ctk.CTkFrame(self)
        self.viewer_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)
        self.viewer_frame.grid_propagate(False)
        self.viewer_frame.configure(width=420, height=420)
        self.viewer_frame.grid_rowconfigure(0, weight=1)
        self.viewer_frame.grid_columnconfigure(0, weight=1)

        self.text_viewer = ctk.CTkTextbox(self.viewer_frame, width=400, height=400)
        self.text_viewer.grid(row=0, column=0, sticky="nsew")
        self.image_label = ctk.CTkLabel(self.viewer_frame, text="")
        self.image_label.grid(row=0, column=0, sticky="nsew")
        self.image_label.grid_remove()
        self.video_panel = None

        # Right: Controls
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=0, column=1, sticky="ne", padx=10, pady=10)
        self.controls_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.controls_frame, text="Input file:").grid(row=0, column=0, sticky="ew", pady=2)
        file_entry = ctk.CTkEntry(self.controls_frame, textvariable=self.file_path, width=220)
        file_entry.grid(row=1, column=0, sticky="ew", pady=2)
        ctk.CTkButton(self.controls_frame, text="Browse", command=self.browse_file).grid(row=1, column=1, padx=5)

        ctk.CTkLabel(self.controls_frame, text="Password:").grid(row=2, column=0, sticky="ew", pady=2)
        ctk.CTkEntry(self.controls_frame, textvariable=self.password, show="*").grid(row=3, column=0, columnspan=2, sticky="ew", pady=2)

        ctk.CTkLabel(self.controls_frame, text="Recovery %:").grid(row=4, column=0, sticky="ew", pady=2)
        ctk.CTkEntry(self.controls_frame, textvariable=self.recovery).grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)

        mode_frame = ctk.CTkFrame(self.controls_frame)
        mode_frame.grid(row=6, column=0, columnspan=2, pady=2)
        ctk.CTkRadioButton(mode_frame, text="Encrypt", variable=self.mode, value="encrypt").pack(side="left", padx=5)
        ctk.CTkRadioButton(mode_frame, text="Decrypt", variable=self.mode, value="decrypt").pack(side="left", padx=5)

        ctk.CTkLabel(self.controls_frame, text="Output directory:").grid(row=7, column=0, sticky="ew", pady=2)
        ctk.CTkEntry(self.controls_frame, textvariable=self.output_dir, width=220).grid(row=8, column=0, sticky="ew", pady=2)
        ctk.CTkButton(self.controls_frame, text="Browse Dir", command=self.browse_output_dir).grid(row=8, column=1, padx=5)
        ctk.CTkButton(self.controls_frame, text="Run", command=self.run_mcfs).grid(row=9, column=0, columnspan=2, pady=10, sticky="ew")

    def browse_file(self):
        if self.mode.get() == "encrypt":
            path = fd.askopenfilename(filetypes=[("All files", "*.*"), ("MCFS files", "*.mcfs")])
        else:
            path = fd.askopenfilename(filetypes=[("MCFS files", "*.mcfs"), ("All files", "*.*")])
        if path:
            self.file_path.set(path)
            if self.mode.get() == "decrypt":
                if not os.path.splitext(path)[1]:
                    path_with_ext = path + ".mcfs"
                    if os.path.exists(path_with_ext):
                        self.file_path.set(path_with_ext)
                        path = path_with_ext
                if path.lower().endswith('.mcfs'):
                    threading.Thread(target=self.auto_view_mcfs, args=(path,), daemon=True).start()
                else:
                    self.show_file_content(path)
            else:
                self.show_file_content(path)

    def browse_output_dir(self):
        dir_path = fd.askdirectory()
        if dir_path:
            self.output_dir.set(dir_path)

    def show_file_content(self, path):
        self.hide_all_viewers()
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                img = Image.open(path)
                img.thumbnail((400, 400))
                from customtkinter import CTkImage
                img_ctk = CTkImage(light_image=img, dark_image=img, size=img.size)
                self.image_label.configure(image=img_ctk)
                self.image_label.image = img_ctk
                self.image_label.grid()
            elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                self.text_viewer.grid_remove()
                self.image_label.grid_remove()
                if self.video_panel:
                    self.video_panel.destroy()
                self.video_panel = ctk.CTkFrame(self.viewer_frame)
                self.video_panel.grid(row=0, column=0, sticky="nsew")
                self.play_video(path)
            else:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                self.text_viewer.grid()
                self.text_viewer.delete("1.0", "end")
                self.text_viewer.insert("end", text)
        except Exception as e:
            self.text_viewer.grid()
            self.text_viewer.delete("1.0", "end")
            self.text_viewer.insert("end", f"Error displaying file: {e}\n")

    def play_video(self, path):
        def video_loop():
            cap = cv2.VideoCapture(path)
            while cap.isOpened() and self.video_panel and self.video_panel.winfo_exists():
                ret, frame = cap.read()
                if not ret:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.thumbnail((400, 400))
                from customtkinter import CTkImage
                img_ctk = CTkImage(light_image=img, dark_image=img, size=img.size)
                if not hasattr(self, 'video_label') or not self.video_label.winfo_exists():
                    self.video_label = ctk.CTkLabel(self.video_panel, text="")
                    self.video_label.pack(expand=True, fill="both")
                self.video_label.configure(image=img_ctk)
                self.video_label.image = img_ctk
                self.video_panel.update_idletasks()
                self.video_panel.update()
                if not self.video_panel.winfo_exists():
                    break
                cv2.waitKey(30)
            cap.release()
            if hasattr(self, 'video_label') and self.video_label.winfo_exists():
                self.video_label.destroy()
        threading.Thread(target=video_loop, daemon=True).start()

    def hide_all_viewers(self):
        self.text_viewer.grid_remove()
        self.image_label.grid_remove()
        if self.video_panel:
            self.video_panel.destroy()
            self.video_panel = None

    def auto_view_mcfs(self, path):
        password = self.password.get()
        try:
            # Try to decrypt and display as text
            import io
            output_buffer = io.StringIO()
            # Patch print to capture output
            import builtins
            old_print = builtins.print
            def fake_print(*args, **kwargs):
                print_str = ' '.join(str(a) for a in args)
                output_buffer.write(print_str + '\n')
            builtins.print = fake_print
            try:
                decrypt_file(path, None, password, view_only=True)
            finally:
                builtins.print = old_print
            content = output_buffer.getvalue().strip()
            if content.startswith('[Non-text file') or 'decode error' in content or not content.strip():
                # Try to decrypt to a temp file and show content
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as tmp:
                    tmp_path = tmp.name
                try:
                    decrypt_file(path, tmp_path, password, view_only=False)
                    self.show_file_content(tmp_path)
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            else:
                self.show_text_output(content)
        except Exception as e:
            self.show_text_output(f"Error viewing mcfs: {e}\n")

    def show_text_output(self, text):
        self.hide_all_viewers()
        self.text_viewer.grid()
        self.text_viewer.delete("1.0", "end")
        self.text_viewer.insert("end", text)

    def run_mcfs(self):
        file = self.file_path.get()
        if not file:
            mb.showerror("Error", "Please select a file.")
            return
        mode = self.mode.get()
        password = self.password.get()
        recovery = self.recovery.get()
        output_dir = self.output_dir.get().strip()
        output = None
        if output_dir:
            base = os.path.basename(file)
            if mode == "encrypt":
                if not base.endswith('.mcfs'):
                    base += '.mcfs'
            output = os.path.join(output_dir, base)
        else:
            if mode == "encrypt":
                output = file + ".mcfs" if not file.endswith('.mcfs') else file
            else:
                output = file.replace('.mcfs', '') if file.endswith('.mcfs') else file

        def run_and_show():
            try:
                if mode == "encrypt":
                    encrypt_file(file, output, password, recovery)
                    self.show_text_output(f"Encrypted to {output}\n")
                else:
                    decrypt_file(file, output, password, False)
                    self.show_text_output(f"Decrypted to {output}\n")
                    if os.path.exists(output):
                        self.show_file_content(output)
            except Exception as e:
                self.show_text_output(f"Error running MCFS: {e}\n")
        threading.Thread(target=run_and_show, daemon=True).start()

def home_widget(parent):
    frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
    ctk.CTkLabel(frame, text="MCFS Quick Access", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
    ctk.CTkLabel(frame, text="Encrypt, decrypt, and view MCFS files.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
    return frame

def main():
    parser = argparse.ArgumentParser(description="MCFS Encrypt/Decrypt Tool")
    subparsers = parser.add_subparsers(dest='command')

    enc = subparsers.add_parser('encrypt', help='Encrypt a file')
    enc.add_argument('input', help='Input file')
    enc.add_argument('output', nargs='?', help='Output .mcfs file')
    enc.add_argument('-p', '--password', required=False, help='Encryption password (optional)')
    enc.add_argument('-r', '--recovery', type=int, default=0, help='Recovery percent (0-30)')

    dec = subparsers.add_parser('decrypt', help='Decrypt a .mcfs file')
    dec.add_argument('input', help='Input .mcfs file')
    dec.add_argument('output', nargs='?', help='Output file')
    dec.add_argument('-p', '--password', required=False, help='Decryption password (optional)')
    dec.add_argument('-v', '--view', action='store_true', help='View decrypted content only (do not save)')

    args = parser.parse_args()
    if args.command == 'encrypt':
        output = args.output or (args.input + '.mcfs')
        encrypt_file(args.input, output, args.password, args.recovery)
    elif args.command == 'decrypt':
        output = args.output or args.input.replace('.mcfs', '')
        decrypt_file(args.input, output, args.password, getattr(args, 'view', False))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
