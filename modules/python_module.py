import customtkinter as ctk
import subprocess
import threading
import shutil
import os
import sys
from tkinter import simpledialog, messagebox

# --- Module Metadata ---
module_version = "1.0.0"
module_name = "Python Manager"
module_emoji = "🐍"
module_icon = None
module_description = "Manage Python installations, pip/uv, and packages."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 4,
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "auto_refresh": {
        "type": "bool",
        "default": True,
        "desc": "Auto-refresh Python list on open"
    }
}

# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = None  # Set to your UI class if exists

class CTkMsgBox(ctk.CTkToplevel):
    @staticmethod
    def show_info(msg, title="Info"):
        win = ctk.CTkToplevel()
        win.title(title)
        win.geometry("400x160")
        win.grab_set()
        ctk.CTkLabel(win, text=msg, font=ctk.CTkFont(size=13)).pack(padx=20, pady=20)
        ctk.CTkButton(win, text="OK", command=win.destroy).pack(pady=10)
        win.wait_window()

    @staticmethod
    def show_error(msg, title="Error"):
        win = ctk.CTkToplevel()
        win.title(title)
        win.geometry("400x160")
        win.grab_set()
        ctk.CTkLabel(win, text=msg, font=ctk.CTkFont(size=13), text_color="#ff5555").pack(padx=20, pady=20)
        ctk.CTkButton(win, text="OK", command=win.destroy).pack(pady=10)
        win.wait_window()

class PythonModuleUI(ctk.CTkFrame):
    """
    UI for managing Python installations and packages.
    """
    def __init__(self, parent, settings=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(self, text="🐍 Python Manager", font=ctk.CTkFont(size=18, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Buttons for actions
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=20)
        btn_frame.grid_columnconfigure((0,1,2,3), weight=1)
        ctk.CTkButton(btn_frame, text="Install Python", command=self.install_python).grid(row=0, column=0, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Install uv", command=self.install_uv).grid(row=0, column=1, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Refresh List", command=self.refresh_pythons).grid(row=0, column=2, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Manage Packages", command=self.open_package_manager).grid(row=0, column=3, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Ensure Python & uv", command=self.ensure_python_and_uv).grid(row=1, column=0, padx=4, pady=4)
        # ctk.CTkButton(btn_frame, text="Scan & Install Missing Pkgs", command=self.scan_and_install_missing_pkgs).grid(row=1, column=1, padx=4, pady=4)

        # List of installed Pythons
        self.python_listbox = ctk.CTkTextbox(self, width=600, height=260, font=ctk.CTkFont(size=13))
        self.python_listbox.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.refresh_pythons()

    def refresh_pythons(self):
        self.python_listbox.configure(state="normal")
        self.python_listbox.delete("1.0", "end")
        pythons = PythonLogic.list_installed_pythons()
        if not pythons:
            self.python_listbox.insert("end", "No Python installations found.\n")
        else:
            for py in pythons:
                self.python_listbox.insert("end", f"{py['path']}  |  Version: {py['version']}\n")
        self.python_listbox.configure(state="disabled")

    def install_python(self):
        class PythonInstallWindow(ctk.CTkToplevel):
            def __init__(win, parent, on_install):
                super().__init__(parent)
                win.title("Install Python Versions")
                win.geometry("340x320")
                win.grab_set()
                ctk.CTkLabel(win, text="Select Python versions to install:", font=ctk.CTkFont(size=14)).pack(pady=(18, 8))
                win.versions = ["3.13","3.12","3.11", "3.10", "3.9", "3.8", "3.7"]
                win.vars = []
                for v in win.versions:
                    var = ctk.BooleanVar()
                    cb = ctk.CTkCheckBox(win, text=f"Python {v}", variable=var)
                    cb.pack(anchor="w", padx=32, pady=2)
                    win.vars.append(var)
                ctk.CTkButton(win, text="Install Selected", command=lambda: win._install(on_install)).pack(pady=18)
            def _install(win, on_install):
                selected = [v for v, var in zip(win.versions, win.vars) if var.get()]
                if selected:
                    win.destroy()
                    on_install(selected)
                else:
                    CTkMsgBox.show_error("Please select at least one version.")
        def on_install(versions):
            def worker():
                self.python_listbox.configure(state="normal")
                for version in versions:
                    self.python_listbox.insert("end", f"\nInstalling Python {version}...\n")
                    self.python_listbox.configure(state="disabled")
                    PythonLogic.install_python_version(version)
                self.refresh_pythons()
            threading.Thread(target=worker, daemon=True).start()
        PythonInstallWindow(self, on_install)

    def install_uv(self):
        class UvInstallWindow(ctk.CTkToplevel):
            def __init__(win, parent, pythons, on_install):
                super().__init__(parent)
                win.title("Install uv")
                win.geometry("420x320")
                win.grab_set()
                ctk.CTkLabel(win, text="Select Python installations to install uv:", font=ctk.CTkFont(size=14)).pack(pady=(18, 8))
                win.vars = []
                win.py_paths = []
                for py in pythons:
                    var = ctk.BooleanVar()
                    cb = ctk.CTkCheckBox(win, text=f"{py['version']} - {py['path']}", variable=var)
                    cb.pack(anchor="w", padx=18, pady=2)
                    win.vars.append(var)
                    win.py_paths.append(py["path"])
                ctk.CTkButton(win, text="Install uv in Selected", command=lambda: win._install(on_install)).pack(pady=18)
            def _install(win, on_install):
                selected = [p for p, var in zip(win.py_paths, win.vars) if var.get()]
                if selected:
                    win.destroy()
                    on_install(selected)
                else:
                    CTkMsgBox.show_error("Please select at least one Python installation.")
        pythons = PythonLogic.list_installed_pythons()
        if not pythons:
            CTkMsgBox.show_error("No Python installations found.")
            return
        def on_install(py_paths):
            def worker():
                self.python_listbox.configure(state="normal")
                for py_path in py_paths:
                    self.python_listbox.insert("end", f"\nInstalling uv in {py_path}...\n")
                    self.python_listbox.configure(state="disabled")
                    PythonLogic.install_uv(py_path)
            threading.Thread(target=worker, daemon=True).start()
        UvInstallWindow(self, pythons, on_install)

    def open_package_manager(self):
        class PythonSelectWindow(ctk.CTkToplevel):
            def __init__(win, parent, pythons, on_select):
                super().__init__(parent)
                win.title("Select Python Instance")
                win.geometry("520x320")
                win.grab_set()
                ctk.CTkLabel(win, text="Select Python instance for package management:", font=ctk.CTkFont(size=14)).pack(pady=(18, 8))
                win.var = ctk.StringVar()
                for py in pythons:
                    rb = ctk.CTkRadioButton(win, text=f"{py['version']} - {py['path']}", variable=win.var, value=py["path"])
                    rb.pack(anchor="w", padx=18, pady=2)
                ctk.CTkButton(win, text="Open Package Manager", command=lambda: win._select(on_select)).pack(pady=18)
            def _select(win, on_select):
                selected = win.var.get()
                if selected:
                    win.destroy()
                    on_select(selected)
                else:
                    CTkMsgBox.show_error("Please select a Python instance.")
        pythons = PythonLogic.list_installed_pythons()
        if not pythons:
            CTkMsgBox.show_error("No Python installations found.")
            return
        def on_select(py_path):
            PackageManagerCTk(self, py_path)
        PythonSelectWindow(self, pythons, on_select)

    def ensure_python_and_uv(self):
        def task_with_error():
            try:
                PythonLogic.ensure_python_and_uv()
                return None
            except Exception as e:
                return str(e)
        ProgressCTk(self, task=task_with_error, on_done=self._on_ensure_done, message="Ensuring Python and uv...")

    def _on_ensure_done(self, error=None):
        if error:
            CTkMsgBox.show_error(f"Error: {error}")
        self.refresh_pythons()
# Progress bar CTk window for long-running tasks
class ProgressCTk(ctk.CTkToplevel):
    def __init__(self, parent, task, on_done=None, message="Working..."):
        super().__init__(parent)
        self.title("Please wait")
        self.geometry("400x160")
        self.grab_set()
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=13)).pack(padx=20, pady=(20, 10))
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(fill="x", padx=40, pady=10)
        self.progress.set(0.1)
        self.after(100, self._run_task, task, on_done)

    def _run_task(self, task, on_done):
        def worker():
            error = None
            try:
                error = task()
            except Exception as e:
                error = str(e)
            finally:
                self.after(0, self._finish, on_done, error)
        threading.Thread(target=worker, daemon=True).start()

    def _finish(self, on_done, error=None):
        self.progress.set(1.0)
        self.destroy()
        if on_done:
            on_done(error)


    def scan_and_install_missing_pkgs(self):
        py_path = PythonLogic.ask_python_path()
        if not py_path:
            return
        def worker():
            self.python_listbox.configure(state="normal")
            self.python_listbox.insert("end", f"\nScanning and installing missing packages in {py_path}...\n")
            self.python_listbox.configure(state="disabled")
            PythonLogic.scan_and_install_missing_pkgs(py_path)
        threading.Thread(target=worker, daemon=True).start()


# All package management windows are now CTkToplevel
class PackageManagerCTk(ctk.CTkToplevel):
    def __init__(self, parent, python_path):
        super().__init__(parent)
        self.title(f"Package Manager - {python_path}")
        self.geometry("600x400")
        self.python_path = python_path
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=f"Python: {self.python_path}", font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10)
        ctk.CTkButton(btn_frame, text="List Packages", command=self.list_packages).grid(row=0, column=0, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Install Package", command=self.install_package).grid(row=0, column=1, padx=4, pady=4)
        ctk.CTkButton(btn_frame, text="Uninstall Package", command=self.uninstall_package).grid(row=0, column=2, padx=4, pady=4)
        self.output = ctk.CTkTextbox(self, width=560, height=260, font=ctk.CTkFont(size=12))
        self.output.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def list_packages(self):
        def worker():
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            pkgs = PythonLogic.list_packages(self.python_path)
            for pkg in pkgs:
                self.output.insert("end", f"{pkg}\n")
            self.output.configure(state="disabled")
        threading.Thread(target=worker, daemon=True).start()

    def install_package(self):
        pkg = simpledialog.askstring("Install Package", "Enter package name:")
        if not pkg:
            return
        def worker():
            self.output.configure(state="normal")
            self.output.insert("end", f"\nInstalling {pkg}...\n")
            self.output.configure(state="disabled")
            PythonLogic.install_package(self.python_path, pkg)
            self.list_packages()
        threading.Thread(target=worker, daemon=True).start()

    def uninstall_package(self):
        pkg = simpledialog.askstring("Uninstall Package", "Enter package name:")
        if not pkg:
            return
        def worker():
            self.output.configure(state="normal")
            self.output.insert("end", f"\nUninstalling {pkg}...\n")
            self.output.configure(state="disabled")
            PythonLogic.uninstall_package(self.python_path, pkg)
            self.list_packages()
        threading.Thread(target=worker, daemon=True).start()

class PythonLogic:
    @staticmethod
    def ensure_python_and_uv():
        """Ensure at least one Python and uv are installed."""
        pythons = PythonLogic.list_installed_pythons()
        # Only consider pythons >= 3.13.4
        min_version = (3, 13, 4)
        def version_tuple(v):
            return tuple(map(int, (v.split("."))))
        filtered = [py for py in pythons if version_tuple(py["version"]) >= min_version]
        if not filtered:
            # Try to install latest Python
            try:
                subprocess.run(["winget", "install", "Python.Python.3.13", "-e", "--accept-package-agreements", "--accept-source-agreements"], check=True)
            except Exception as e:
                CTkMsgBox.show_error(f"Failed to install Python: {e}")
                return
            pythons = PythonLogic.list_installed_pythons()
            filtered = [py for py in pythons if version_tuple(py["version"]) >= min_version]
        for py in filtered:
            try:
                subprocess.run([py["path"], "-m", "pip", "install", "uv"], check=True)
            except Exception as e:
                CTkMsgBox.show_error(f"Failed to install uv in {py['path']}: {e}")

    @staticmethod
    def scan_and_install_missing_pkgs(python_path):
        """Scan for common packages and install any missing ones."""
        required = ["customtkinter", "requests", "pillow", "yt-dlp", "uv"]
        # Map import names to PyPI package names (shared with handler)
        install_name_map = {
            "cv2": "opencv-python",
            "PIL": "Pillow",
            "Crypto": "pycryptodome",
            "optparse": "optparse",
        }
        try:
            out = subprocess.check_output([python_path, "-m", "pip", "freeze"], text=True)
            installed = set([line.split("==")[0].lower() for line in out.strip().splitlines() if "==" in line])
        except Exception:
            installed = set()
        missing = [pkg for pkg in required if pkg.lower() not in installed]
        if not missing:
            messagebox.showinfo("Packages", "All required packages are already installed.")
            return
        # Map missing to install names
        install_pkgs = [install_name_map.get(m, m) for m in missing]
        try:
            subprocess.run([python_path, "-m", "pip", "install"] + install_pkgs, check=True)
            messagebox.showinfo("Packages", f"Installed missing packages: {', '.join(install_pkgs)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install packages: {e}")
    @staticmethod
    def list_installed_pythons():
        """Return a list of installed Python interpreters with their versions."""
        pythons = []
        candidates = set()
        # Check PATH for python executables
        for path in os.environ["PATH"].split(os.pathsep):
            for exe_name in ("python.exe", "python3.exe", "python", "python3"):
                exe_path = os.path.join(path, exe_name)
                if os.path.isfile(exe_path) and os.access(exe_path, os.X_OK):
                    candidates.add(os.path.abspath(exe_path))
        # Windows: check common install folders
        if sys.platform == "win32":
            possible_dirs = [
                os.path.join(os.environ.get("LocalAppData", ""), "Programs", "Python"),
                os.path.join(os.environ.get("ProgramFiles", ""), "Python"),
                os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Python"),
            ]
            for d in possible_dirs:
                if os.path.isdir(d):
                    for sub in os.listdir(d):
                        exe = os.path.join(d, sub, "python.exe")
                        if os.path.isfile(exe) and os.access(exe, os.X_OK):
                            candidates.add(os.path.abspath(exe))
        # Remove any directories, only keep files that are executable
        valid_candidates = [exe for exe in candidates if os.path.isfile(exe) and os.access(exe, os.X_OK)]
        # Get version info
        for exe in valid_candidates:
            try:
                out = subprocess.check_output([exe, "--version"], stderr=subprocess.STDOUT, text=True)
                version = out.strip().replace("Python ", "")
                pythons.append({"path": exe, "version": version})
            except Exception:
                continue
        return pythons

    @staticmethod
    def install_python_version(version):
        """Install a specific Python version using winget (Windows only)."""
        args = ["winget", "install", f"Python.Python.{version}"]
        try:
            subprocess.run(args, check=True)
            messagebox.showinfo("Success", f"Python {version} installed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install Python {version}: {e}")

    @staticmethod
    def ask_python_path():
        pythons = PythonLogic.list_installed_pythons()
        if not pythons:
            messagebox.showerror("Error", "No Python installations found.")
            return None
        if len(pythons) == 1:
            return pythons[0]["path"]
        # Ask user to select
        options = [f"{py['version']} - {py['path']}" for py in pythons]
        choice = simpledialog.askstring("Select Python", "\n".join(f"{i+1}. {opt}" for i, opt in enumerate(options)) + "\nEnter number:")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(pythons):
                return pythons[idx]["path"]
        except Exception:
            pass
        return None

    @staticmethod
    def install_uv(python_path):
        try:
            subprocess.run([python_path, "-m", "pip", "install", "uv"], check=True)
            messagebox.showinfo("Success", f"uv installed in {python_path}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install uv: {e}")

    @staticmethod
    def list_packages(python_path):
        try:
            out = subprocess.check_output([python_path, "-m", "pip", "list"], text=True)
            return out.strip().splitlines()
        except Exception as e:
            return [f"Error: {e}"]

    @staticmethod
    def install_package(python_path, package):
        try:
            subprocess.run([python_path, "-m", "uv", "pip", "install", "--system", package], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to install {package}: {e}")

    @staticmethod
    def uninstall_package(python_path, package):
        try:
            subprocess.run([python_path, "-m", "uv", "pip", "uninstall" ,"--system", "-y", package], check=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to uninstall {package}: {e}")

def home_widget(parent):
    frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
    ctk.CTkLabel(frame, text="Python Manager Widget", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
    ctk.CTkLabel(frame, text="Manage Python installations and packages.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
    return frame
