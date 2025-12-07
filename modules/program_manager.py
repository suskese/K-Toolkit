import customtkinter as ctk
import tkinter.filedialog as filedialog
import tkinter.simpledialog as simpledialog
import tkinter.messagebox as messagebox
import threading
import os
import subprocess
from PIL import Image
import certifi
import ssl
from core.emoji import emoji_

# --- Module Metadata ---
module_name = "Program Manager"
module_icon = "icon.png"
module_emoji = "🎲"
module_version = "1.0.0"
module_description = "Install, uninstall, and manage common programs."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 5,
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "show_hidden": {
        "type": "bool",
        "default": False,
        "desc": "Show hidden/system programs"
    }
}

# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = None  # Set to your UI class if exists

# Use program detection logic from core_utilities
from core import program_detection

folder_emoji = emoji_("📁")
trash_emoji = emoji_("     🗑️")
reinstall_emoji = emoji_("     ♻️")
install_emoji = emoji_("📥")

os.environ['SSL_CERT_FILE'] = certifi.where()
ssl._create_default_https_context = ssl.create_default_context

class ProgramManagerUI(ctk.CTkFrame):
    def __init__(self, parent, settings=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(self, text="Manage Programs", font=ctk.CTkFont(size=18, weight="bold"))
        label.pack(pady=(20, 10))

        # Search bar
        self.search_var = ctk.StringVar()
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(search_frame, text="Search:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=220)
        search_entry.pack(side="left", padx=(0, 6))
        search_entry.bind("<KeyRelease>", lambda e: self.refresh_programs())

        # Improved scrollable frame for program panels
        self.scrollable = ctk.CTkScrollableFrame(self, fg_color="transparent", width=1, height=1)
        self.scrollable.pack(fill="both", expand=True, padx=8, pady=8, anchor="nw")
        self.scrollable.grid_columnconfigure((0,1), weight=1)
        self.scrollable.grid_rowconfigure(0, weight=1)

        # List of programs to manage (with icons, winget ids, etc.)
        self.programs = [
            {
                "name": "FFmpeg",
                "desc": "Required for video/audio processing.",
                "exe": "ffmpeg.exe",
                "winget": "Gyan.FFmpeg",
                "icon": "assets/icon.png"
            },
            {
                "name": "Everything",
                "desc": "Ultra-fast file search for Windows.",
                "exe": "Everything.exe",
                "winget": "voidtools.Everything",
                "icon": "assets/icon.png"
            },
            {
                "name": "7-Zip",
                "desc": "Popular file archiver.",
                "exe": "7z.exe",
                "winget": "7zip.7zip",
                "icon": "assets/icon.png"
            },
            {
                "name": "VLC",
                "desc": "Versatile media player.",
                "exe": "vlc.exe",
                "winget": "VideoLAN.VLC",
                "icon": "assets/icon.png"
            },
            {
                "name": "Reg Organizer",
                "desc": "Advanced system utility for Windows registry.",
                "exe": "RegOrganizer.exe",
                "winget": "ChemTableSoftware.RegOrganizer",
                "icon": "assets/icon.png"
            },
            {
                "name": "WizTree",
                "desc": "Disk space analyzer.",
                "exe": "WizTree64.exe",
                "winget": "AntibodySoftware.WizTree",
                "icon": "assets/icon.png"
            },
            {
                "name": "Prism Launcher",
                "desc": "Minecraft launcher.",
                "exe": "PrismLauncher.exe",
                "winget": "PrismLauncher.PrismLauncher",
                "icon": "assets/icon.png"
            },
            {
                "name": "IntelliJ IDEA",
                "desc": "Java IDE by JetBrains.",
                "exe": "idea64.exe",
                "winget": "JetBrains.IntelliJIDEA.Community",
                "icon": "assets/icon.png"
            },
            {
                "name": "Visual Studio Code",
                "desc": "Popular code editor.",
                "exe": "Code.exe",
                "winget": "Microsoft.VisualStudioCode",
                "icon": "assets/icon.png"
            },
            {
                "name": "Visual Studio 2022",
                "desc": "Advanced code editor.",
                "exe": "devenv.exe",
                "winget": "Microsoft.VisualStudio.2022.Community",
                "icon": "assets/icon.png"
            },
            {
                "name": "SkyClient",
                "desc": "Minecraft modpack installer.",
                "exe": "SkyClient.exe",
                "winget": None,
                "icon": "assets/icon.png",
                "Source": "https://github.com/SkyblockClient/SkyClient-Windows/releases/latest"
            },
            {
                "name": "Discord",
                "desc": "Popular chat and voice app.",
                "exe": "Discord.exe",
                "winget": "Discord.Discord",
                "icon": "assets/icon.png"
            },
            {
                "name": "Google Chrome",
                "desc": "Web browser by Google.",
                "exe": "chrome.exe",
                "winget": "Google.Chrome",
                "icon": "assets/icon.png"
            },
            {
                "name": "Opera GX",
                "desc": "Gaming web browser by Opera.",
                "exe": "opera.exe",
                "winget": "Opera.OperaGX",
                "icon": "assets/icon.png"
            },
            {
                "name": "Brave",
                "desc": "Privacy-focused web browser.",
                "exe": "brave.exe",
                "winget": "Brave.Brave",
                "icon": "assets/icon.png"
            },
            {
                "name": "WinSCP",
                "desc": "SFTP client and FTP client for Windows.",
                "exe": "WinSCP.exe",
                "winget": "WinSCP.WinSCP",
                "icon": "assets/icon.png"
            },
            {
                "name": "K-Lite Codec Pack Mega",
                "desc": "Comprehensive codec pack.",
                "exe": "klcp_mega.exe",
                "winget": "CodecGuide.K-LiteCodecPack.Mega",
                "icon": "assets/icon.png"
            },
            {
                "name": "Python",
                "desc": "Install multiple Python versions (3.8.x - 3.13.x) with pip and tk.",
                "exe": "python.exe",
                "winget": "Python.Python.3",
                "icon": "assets/icon.png",
                "python_multi": True
            },
            {
                "name": "Eclipse Temurin JDK 8",
                "desc": "Eclipse Adoptium OpenJDK 8.",
                "exe": "java.exe",
                "winget": "EclipseAdoptium.Temurin.8.JDK",
                "icon": "assets/icon.png"
            },
            {
                "name": "Eclipse Temurin JDK 11",
                "desc": "Eclipse Adoptium OpenJDK 11.",
                "exe": "java.exe",
                "winget": "EclipseAdoptium.Temurin.11.JDK",
                "icon": "assets/icon.png"
            },
            {
                "name": "Eclipse Temurin JDK 17",
                "desc": "Eclipse Adoptium OpenJDK 17.",
                "exe": "java.exe",
                "winget": "EclipseAdoptium.Temurin.17.JDK",
                "icon": "assets/icon.png"
            },
            {
                "name": "Eclipse Temurin JDK 21",
                "desc": "Eclipse Adoptium OpenJDK 21.",
                "exe": "java.exe",
                "winget": "EclipseAdoptium.Temurin.21.JDK",
                "icon": "assets/icon.png"
            },
        ]

        # Detect installed programs at startup
        program_names = [prog["name"] for prog in self.programs]
        self.detected = program_detection.detect_programs_by_name(program_names)

        self.refresh_programs()

    def refresh_programs(self):
        # Clear previous widgets
        for widget in self.scrollable.winfo_children():
            widget.destroy()
        # Filter by search
        query = self.search_var.get().lower()
        filtered = [p for p in self.programs if query in p["name"].lower() or query in p["desc"].lower()]
        # Two per row
        for i, prog in enumerate(filtered):
            col = i % 2
            row = i // 2
            panel = ctk.CTkFrame(self.scrollable, fg_color="#232323", corner_radius=18, border_width=2, border_color="#444444")
            panel.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            panel.grid_columnconfigure(1, weight=1)
            panel.grid_rowconfigure(4, weight=1)
            panel.configure(width=370, height=180)
            # Icon (placeholder, can load from file if available)
            icon_path = prog.get("icon")
            if icon_path and os.path.exists(icon_path):
                img = ctk.CTkImage(Image.open(icon_path), size=(48,48))
                icon = ctk.CTkLabel(panel, image=img, text="")
            else:
                icon = ctk.CTkLabel(panel, text="🛠️", font=ctk.CTkFont(size=32))
            icon.grid(row=0, column=0, rowspan=2, padx=12, pady=8, sticky="nw")
            # Name & Description
            ctk.CTkLabel(panel, text=prog["name"], font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=1, sticky="nw", padx=(0,8), pady=(8,0))
            ctk.CTkLabel(panel, text=prog["desc"], font=ctk.CTkFont(size=12), wraplength=220, justify="left").grid(row=1, column=1, sticky="nw", padx=(0,8))
            # Path & status (wrap long paths)
            detected_path = self.detected.get(prog["name"])
            path_str = detected_path if detected_path else "Not installed"
            import textwrap
            wrapped_path = "\n".join(textwrap.wrap(str(path_str), width=42))
            ctk.CTkLabel(panel, text=f"Path: {wrapped_path}", font=ctk.CTkFont(size=11), text_color="#bbbbbb", justify="left", wraplength=320).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(4,0))
            # Buttons
            btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
            btn_frame.grid(row=3, column=0, columnspan=2, pady=(6,2), padx=8, sticky="ew")
            btn_frame.grid_columnconfigure((0,1,2,3), weight=1)
            btn_style = {"height":32, "width":60, "corner_radius":8, "font":ctk.CTkFont(size=13), "fg_color":"transparent", "hover_color":"#232323"}
            ctk.CTkButton(btn_frame, text="", image=install_emoji, command=lambda p=prog: self.install_program(p), **btn_style).grid(row=0, column=0, padx=2, pady=0, sticky="ew")
            ctk.CTkButton(btn_frame, text="", image=reinstall_emoji, command=lambda p=prog: self.reinstall_program(p), **btn_style).grid(row=0, column=1, padx=2, pady=0, sticky="ew")
            ctk.CTkButton(btn_frame, text="", image=trash_emoji, command=lambda p=prog: self.uninstall_program(p), **btn_style).grid(row=0, column=2, padx=2, pady=0, sticky="ew")
            ctk.CTkButton(btn_frame, text="Open", width=70, height=32, corner_radius=8, font=ctk.CTkFont(size=13), fg_color="transparent", hover_color="#232323", command=lambda p=prog: self.open_program(p)).grid(row=0, column=3, padx=2, pady=0, sticky="ew")

    def run_winget_command(self, args, title="Operation"):
        progress_win = ctk.CTkToplevel(self)
        progress_win.title(title)
        progress_win.geometry("600x400")
        progress_win.resizable(True, True)
        progress_text = ctk.CTkTextbox(progress_win, width=580, height=340, font=ctk.CTkFont(size=12))
        progress_text.pack(padx=10, pady=10, fill="both", expand=True)
        progress_text.insert("end", f"Running: winget {' '.join(args)}\n\n")
        progress_text.configure(state="disabled")
        close_btn = ctk.CTkButton(progress_win, text="Close", state="disabled", command=progress_win.destroy)
        close_btn.pack(pady=(0,10))

        def worker():
            try:
                cmd = ["winget"] + args
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
                last_line = ""
                for raw_line in proc.stdout:
                    try:
                        line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
                    except Exception:
                        line = str(raw_line)
                    # Filter out lines that are just progress bars or spinners
                    if (set(line.strip()) <= set(" -\\|/") or
                        all(ord(c) > 127 for c in line.strip()) or
                        not line.strip()):
                        continue
                    # Collapse repeated lines
                    if line.strip() == last_line.strip():
                        continue
                    last_line = line
                    progress_text.configure(state="normal")
                    progress_text.insert("end", line)
                    progress_text.see("end")
                    progress_text.configure(state="disabled")
                proc.wait()
                progress_text.configure(state="normal")
                if proc.returncode == 0:
                    progress_text.insert("end", f"\nSuccess!\n")
                else:
                    progress_text.insert("end", f"\nError (code {proc.returncode})\n")
                progress_text.configure(state="disabled")
                close_btn.configure(state="normal")
            except Exception as e:
                progress_text.configure(state="normal")
                progress_text.insert("end", f"Exception: {e}\n")
                progress_text.configure(state="disabled")
                close_btn.configure(state="normal")
        threading.Thread(target=worker, daemon=True).start()

    def install_program(self, prog):
        winget_id = prog.get('winget')
        source_url = prog.get('Source')
        if source_url:
            import webbrowser
            webbrowser.open(source_url)
            messagebox.showinfo("Manual Download", f"Opened source page for {prog['name']} in your browser.")
            return
        if prog.get('python_multi'):
            self.install_python_multi()
            return
        if winget_id:
            self.run_winget_command(["install", "--id", winget_id, "-e", "--accept-package-agreements", "--accept-source-agreements"], title=f"Install {prog['name']}")
        else:
            messagebox.showinfo("Install", f"Manual install required for {prog['name']}.")

    def reinstall_program(self, prog):
        winget_id = prog.get('winget')
        if prog.get('python_multi'):
            self.install_python_multi(reinstall=True)
            return
        if winget_id:
            self.run_winget_command(["install", "--id", winget_id, "-e", "--force", "--accept-package-agreements", "--accept-source-agreements"], title=f"Reinstall {prog['name']}")
        else:
            messagebox.showinfo("Reinstall", f"Manual reinstall required for {prog['name']}.")

    def uninstall_program(self, prog):
        winget_id = prog.get('winget')
        if prog.get('python_multi'):
            self.uninstall_python_multi()
            return
        if winget_id:
            self.run_winget_command(["uninstall", "--id", winget_id, "-e"], title=f"Uninstall {prog['name']}")
        else:
            messagebox.showinfo("Uninstall", f"Manual uninstall required for {prog['name']}.")
    
    def install_python_multi(self, reinstall=False):
        version = simpledialog.askstring("Python Version", "Enter Python version to install (e.g. 3.8.10, 3.9.13, 3.10.11, 3.11.9, 3.12.3, 3.13.0):")
        if not version:
            return
        args = ["install", "--id", "Python.Python.3", "-e", "--accept-package-agreements", "--accept-source-agreements"]
        if version:
            args += ["--version", version]
        if reinstall:
            args += ["--force"]
        self.run_winget_command(args, title=f"Install Python {version}")
        if messagebox.askyesno("Python Modules", "Install common modules (customtkinter, yt-dlp, requests, pillow)?"):
            self.install_python_modules(version)

    def uninstall_python_multi(self):
        version = simpledialog.askstring("Python Version", "Enter Python version to uninstall (e.g. 3.8.10, 3.9.13, 3.10.11, 3.11.9, 3.12.3, 3.13.0):")
        if not version:
            return
        args = ["uninstall", "--id", "Python.Python.3", "-e"]
        if version:
            args += ["--version", version]
        self.run_winget_command(args, title=f"Uninstall Python {version}")

    def install_python_modules(self, version):
        import shutil
        py_exec = shutil.which(f"python{version[:3]}") or shutil.which("python")
        if not py_exec:
            messagebox.showerror("Python Modules", f"Could not find python executable for {version}.")
            return
        modules = ["customtkinter", "yt-dlp", "requests", "pillow"]
        def worker():
            try:
                for mod in modules:
                    subprocess.run([py_exec, "-m", "pip", "install", mod], check=False)
                messagebox.showinfo("Python Modules", f"Modules installed for Python {version}.")
            except Exception as e:
                messagebox.showerror("Python Modules", f"Error: {e}")
        threading.Thread(target=worker, daemon=True).start()

    def open_program(self, prog):
        detected_path = self.detected.get(prog["name"])
        if detected_path and os.path.exists(detected_path):
            try:
                if os.name == "nt":
                    os.startfile(detected_path)
                else:
                    subprocess.Popen([detected_path])
            except Exception as e:
                messagebox.showerror("Open Program", f"Failed to open: {e}")
        else:
            messagebox.showinfo("Open Program", "Program not found or not installed.")

def home_widget(parent):
    frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
    ctk.CTkLabel(frame, text="Program Manager Widget", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
    ctk.CTkLabel(frame, text="Install, uninstall, and manage programs.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
    return frame
