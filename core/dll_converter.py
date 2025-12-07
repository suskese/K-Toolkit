import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
import subprocess
import gc
import ast

# --- Module Metadata ---
module_version = "1.0.0"
module_name = "DLL Converter"
module_emoji = "🛠️"
module_icon = None
module_description = "Convert Python modules to DLL (.pyd) using Cython and package dependencies as .pex files in ./libs."

home_widgets = {
    "show": True,
    "order": 99,
    "desc": module_description,
}

mod_settings = {
    "cythonize_level": {
        "type": "str",
        "default": "3",
        "desc": "Cython language level (2 or 3)"
    },
    "hidden_imports": {
        "type": "str",
        "default": "",
        "desc": "Comma-separated extra packages to include and package as .pex (e.g. numpy, customtkinter)"
    }
}

class DLLConverterUI(ctk.CTkFrame):
    # Mapping from import name to PyPI package name
    IMPORT_TO_PYPI = {
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "skimage": "scikit-image",
        "Crypto": "pycryptodome",
        "yaml": "PyYAML",
        "Image": "Pillow",
        "lxml": "lxml",
        "bs4": "beautifulsoup4",
        "matplotlib": "matplotlib",
        "scipy": "scipy",
        "sklearn": "scikit-learn",
        "dateutil": "python-dateutil",
        "requests": "requests",
        "customtkinter": "customtkinter",
    }

    def __init__(self, parent, settings=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.imported_modules = []
        self.check_vars = {}
        self.checkboxes_frame = None
        self.pip_cmd = self.detect_pip_command()
        self.setup_ui()

    def detect_pip_command(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[DLLConverter] Using: {sys.executable} -m pip")
            return [sys.executable, "-m", "pip"]
        except Exception as e:
            print(f"[DLLConverter] python -m pip failed: {e}")
            candidates = [
                os.path.join(os.path.dirname(sys.executable), "pip.exe"),
                os.path.join(os.path.dirname(sys.executable), "Scripts", "pip.exe"),
                os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Scripts", "pip.exe"),
            ]
            for pip_exe in candidates:
                print(f"[DLLConverter] Trying pip.exe at: {pip_exe}")
                if os.path.exists(pip_exe):
                    try:
                        subprocess.check_call([pip_exe, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"[DLLConverter] Using: {pip_exe}")
                        return [pip_exe]
                    except Exception as e2:
                        print(f"[DLLConverter] pip.exe at {pip_exe} failed: {e2}")
            try:
                subprocess.check_call(["pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"[DLLConverter] Using: pip (from PATH)")
                return ["pip"]
            except Exception as e3:
                print(f"[DLLConverter] pip on PATH failed: {e3}")
            messagebox.showerror("Error", f"pip is not available in this environment.\nPython: {sys.executable}\nError: {e}")
            return None

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(self, text="DLL Converter", font=ctk.CTkFont(size=18, weight="bold"))
        label.grid(row=0, column=0, padx=20, pady=(20, 10))
        desc = ctk.CTkLabel(self, text=module_description, font=ctk.CTkFont(size=13))
        desc.grid(row=1, column=0, padx=20, pady=(0, 10))

        self.select_btn = ctk.CTkButton(self, text="Select Python Module", command=self.select_module)
        self.select_btn.grid(row=2, column=0, padx=20, pady=10)

        self.checkboxes_frame = ctk.CTkFrame(self)
        self.checkboxes_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.convert_btn = ctk.CTkButton(self, text="Convert to DLL (.pyd) & .pex", command=self.convert_module, state="disabled")
        self.convert_btn.grid(row=4, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.grid(row=5, column=0, padx=20, pady=10)

        self.selected_module = None

    def select_module(self):
        file_path = filedialog.askopenfilename(
            title="Select Python Module",
            filetypes=[("Python Files", "*.py")],
            initialdir=os.path.abspath(os.path.join(os.getcwd(), "modules"))
        )
        if file_path:
            self.selected_module = file_path
            self.status_label.configure(text=f"Selected: {os.path.basename(file_path)}")
            self.convert_btn.configure(state="normal")
            self.detect_imports(file_path)
        else:
            self.selected_module = None
            self.status_label.configure(text="No module selected.")
            self.convert_btn.configure(state="disabled")
            self.clear_checkboxes()

    def clear_checkboxes(self):
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()
        self.check_vars = {}

    def detect_imports(self, file_path):
        self.clear_checkboxes()
        third_party = self.get_third_party_imports(file_path)
        self.imported_modules = third_party
        if not third_party:
            label = ctk.CTkLabel(self.checkboxes_frame, text="No third-party imports detected.")
            label.pack(anchor="w", padx=4, pady=2)
            return
        label = ctk.CTkLabel(self.checkboxes_frame, text="Third-party imports:", font=ctk.CTkFont(size=12, weight="bold"))
        label.pack(anchor="w", padx=4, pady=(2, 4))
        for mod in third_party:
            var = tk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(self.checkboxes_frame, text=mod, variable=var)
            chk.pack(anchor="w", padx=8, pady=2)
            self.check_vars[mod] = var

    def get_third_party_imports(self, file_path):
        stdlib = set(sys.builtin_module_names)
        stdlib.update({
            'os', 'sys', 'math', 'json', 're', 'subprocess', 'threading', 'time', 'tkinter', 'ctypes', 'gc', 'logging', 'collections', 'itertools', 'functools', 'typing', 'pathlib', 'shutil', 'random', 'datetime', 'inspect', 'platform', 'traceback', 'unittest', 'email', 'http', 'urllib', 'xml', 'csv', 'argparse', 'socket', 'queue', 'multiprocessing', 'asyncio', 'contextlib', 'enum', 'abc', 'pprint', 'glob', 'tempfile', 'getpass', 'hashlib', 'hmac', 'base64', 'struct', 'signal', 'weakref', 'zipfile', 'codecs', 'configparser', 'copy', 'decimal', 'difflib', 'doctest', 'fileinput', 'fractions', 'heapq', 'html', 'imghdr', 'locale', 'mailbox', 'mmap', 'numbers', 'pickle', 'selectors', 'smtplib', 'sqlite3', 'ssl', 'statistics', 'string', 'tarfile', 'textwrap', 'uuid', 'webbrowser', 'wsgiref', 'zlib', 'zoneinfo', 'dataclasses', 'concurrent', 'importlib', 'site', 'distutils', 'setuptools', 'venv', 'pip', 'cython', 'pex'
        })
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        third_party = [mod for mod in sorted(imports) if mod not in stdlib]
        return third_party

    def convert_module(self):
        if not self.selected_module:
            messagebox.showerror("Error", "No module selected.")
            return
        self.status_label.configure(text="Converting...")
        self.update()
        try:
            try:
                import Cython
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "cython"])

            # Ask user for archive type
            archive_type = tk.StringVar(value="zip")
            def set_type(val):
                archive_type.set(val)
                top.destroy()
            top = tk.Toplevel(self)
            top.title("Select Archive Type")
            tk.Label(top, text="How should dependencies be packed?").pack(padx=20, pady=10)
            tk.Button(top, text=".zip (recommended for native packages)", command=lambda: set_type("zip")).pack(fill="x", padx=20, pady=5)
            tk.Button(top, text=".pex (for pure Python)", command=lambda: set_type("pex")).pack(fill="x", padx=20, pady=5)
            top.grab_set()
            self.wait_window(top)

            hidden_imports = self.settings.get("hidden_imports", "")
            hidden_imports_list = [pkg.strip() for pkg in hidden_imports.split(",") if pkg.strip()]
            checked_imports = [mod for mod, var in self.check_vars.items() if var.get()]
            all_imports = list(set(hidden_imports_list + checked_imports))
            libs_dir = os.path.abspath("libs")
            if not os.path.exists(libs_dir):
                os.makedirs(libs_dir)

            module_path = self.selected_module
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            if module_name in sys.modules:
                del sys.modules[module_name]
                gc.collect()

            setup_code = (
                "from setuptools import setup\n"
                "from Cython.Build import cythonize\n"
                f"setup(\n    ext_modules=cythonize('{module_path}', language_level={self.settings.get('cythonize_level', '3')})\n)\n"
            )
            setup_path = os.path.join(os.path.dirname(module_path), "setup_cython_temp.py")
            with open(setup_path, "w") as f:
                f.write(setup_code)
            cmd = [sys.executable, setup_path, "build_ext", "--inplace"]
            result = subprocess.run(cmd, cwd=os.path.dirname(module_path), capture_output=True, text=True)
            gc.collect()
            if result.returncode == 0:
                self.status_label.configure(text=f"Conversion successful! .pyd created in {os.path.dirname(module_path)}")
                messagebox.showinfo("Success", f"DLL (.pyd) created for {module_name}.")
            else:
                self.status_label.configure(text="Conversion failed.")
                messagebox.showerror("Error", result.stderr)
            os.remove(setup_path)

            for mod_name in all_imports:
                pkg_name = self.IMPORT_TO_PYPI.get(mod_name, mod_name)
                self.status_label.configure(text=f"Packaging {pkg_name} as {archive_type.get()} in ./libs...")
                install_dir = os.path.join(libs_dir, pkg_name)
                if not self.pip_cmd:
                    self.status_label.configure(text=f"pip is not available. Skipping {pkg_name}.")
                    continue
                pip_success = False
                if archive_type.get() == "zip":
                    try:
                        subprocess.check_call(self.pip_cmd + ["install", pkg_name, "-t", install_dir])
                        pip_success = True
                    except Exception as e:
                        self.status_label.configure(text=f"Failed to pip install {pkg_name}: {e}")
                        continue
                    import shutil
                    shutil.make_archive(os.path.join(libs_dir, pkg_name), 'zip', install_dir)
                    shutil.rmtree(install_dir)
                elif archive_type.get() == "pex":
                    try:
                        subprocess.check_call(self.pip_cmd + ["install", "pex"])
                    except Exception:
                        pass
                    pex_path = os.path.join(libs_dir, f"{pkg_name}.pex")
                    pex_cmd = [sys.executable, "-m", "pex", pkg_name, "-o", pex_path]
                    subprocess.run(pex_cmd, capture_output=True, text=True)
            self.status_label.configure(text="All done!")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}")
            messagebox.showerror("Error", str(e))

    @staticmethod
    def home_widget(parent):
        frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
        ctk.CTkLabel(frame, text="DLL Converter", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkLabel(frame, text="Convert Python modules to DLL (.pyd) and package dependencies as .pex in ./libs.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
        return frame

widget_display = home_widgets
settings_config = mod_settings
ModuleUI = DLLConverterUI
