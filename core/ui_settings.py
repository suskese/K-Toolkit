import customtkinter as ctk
import os
import tkinter.filedialog as filedialog
import tkinter as tk
from core.emoji import emoji_
from PIL import Image

folder_emoji=emoji_("📁")
save_emoji=emoji_("💾")

class SettingsTab(ctk.CTkFrame):

    def __init__(self, parent, settings):
        import shutil
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        # --- Tabs for Settings ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)
        # --- General Tab ---
        general_tab = self.tabs.add("General")

        # --- Mod Configs Tab ---
        mod_configs_tab = self.tabs.add("Mod Configs")
        mod_configs_frame = ctk.CTkFrame(mod_configs_tab, fg_color="#232323", corner_radius=8)
        mod_configs_frame.pack(fill="both", expand=True, padx=30, pady=10)
        ctk.CTkLabel(mod_configs_frame, text="Module Configurations", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        import importlib.util, glob
        module_files = glob.glob(os.path.join("modules", "*.py"))
        pyd_files = glob.glob(os.path.join("modules", "*.pyd"))
        module_files += pyd_files
        # --- Home Page Widget Visibility Section ---
        home_section = ctk.CTkFrame(mod_configs_frame, fg_color="#232323", corner_radius=8)
        home_section.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(home_section, text="Home Page", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=10, pady=(0, 2))
        # Load current state from settings
        home_widgets_enabled = self.settings.get('home_widgets_enabled', {})
        # List all modules for toggling
        for mod_path in module_files:
            mod_name = os.path.splitext(os.path.basename(mod_path))[0]
            if mod_name.startswith("__"):
                continue
            # For .pyd, skip if .py with same name already loaded
            if mod_path.endswith('.pyd') and os.path.exists(os.path.join("modules", f"{mod_name}.py")):
                continue
            spec = importlib.util.spec_from_file_location(mod_name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Failed to load module {mod_name}: {e}")
                continue
            mod_disp = getattr(mod, "module_name", mod_name)
            mod_id = getattr(mod, "module_name", mod_name)
            row = ctk.CTkFrame(home_section, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=2)
            ctk.CTkLabel(row, text=mod_disp, font=ctk.CTkFont(size=11)).pack(side="left")
            var = ctk.BooleanVar(value=home_widgets_enabled.get(mod_id, True))
            def make_callback(mid, v):
                def cb():
                    # Save to settings and update
                    home_widgets_enabled[mid] = v.get()
                    self.settings.set('home_widgets_enabled', home_widgets_enabled)
                return cb
            cb = make_callback(mod_id, var)
            ctk.CTkCheckBox(row, variable=var, text="Show on Home", command=cb).pack(side="left", padx=8)

        # FFmpeg Path
        ffmpeg_frame = ctk.CTkFrame(general_tab, fg_color="#232323", corner_radius=8)
        ffmpeg_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(ffmpeg_frame, text="FFmpeg Path for Downloader", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))

        # Auto-detect ffmpeg if not set
        ffmpeg_path_setting = self.settings.get("ffmpeg_path", "")
        ffmpeg_path_found = shutil.which("ffmpeg")
        if not ffmpeg_path_setting and ffmpeg_path_found:
            self.settings.set("ffmpeg_path", "PATH")
            ffmpeg_path_setting = "PATH"

        ffmpeg_var = ctk.StringVar(value=ffmpeg_path_setting)
        ffmpeg_entry = ctk.CTkEntry(ffmpeg_frame, textvariable=ffmpeg_var, width=400)
        ffmpeg_entry.pack(side="left", padx=(10, 5), pady=(0, 10))
        def browse_ffmpeg():
            path = filedialog.askopenfilename(title="Select ffmpeg.exe", filetypes=[("ffmpeg.exe", "ffmpeg.exe"), ("All files", "*")])
            if path:
                ffmpeg_var.set(path)
        ctk.CTkButton(ffmpeg_frame, image=folder_emoji, text="", command=browse_ffmpeg, fg_color="#1f6aa5", width=70).pack(side="right", padx=10, pady=(0, 10))
        def save_ffmpeg():
            val = ffmpeg_var.get().strip()
            self.settings.set("ffmpeg_path", val)
        ctk.CTkButton(ffmpeg_frame, image=save_emoji, text="", command=save_ffmpeg, fg_color="#2a8cdb", width=70).pack(side="right", padx=0, pady=(0, 10))

        # Video Downloader Default Path
        vdl_frame = ctk.CTkFrame(general_tab, fg_color="#232323", corner_radius=8)
        vdl_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(vdl_frame, text="Default Video Download Path", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        vdl_var = ctk.StringVar(value=self.settings.get("video_download_path", ""))
        vdl_entry = ctk.CTkEntry(vdl_frame, textvariable=vdl_var, width=400)
        vdl_entry.pack(side="left", padx=(10, 5), pady=(0, 10))
        def browse_vdl():
            path = filedialog.askdirectory(title="Select Download Directory")
            if path:
                vdl_var.set(path)
        ctk.CTkButton(vdl_frame, image=folder_emoji,text="", command=browse_vdl, fg_color="#1f6aa5",width=70).pack(side="right", padx=10, pady=(0, 10))
        def save_vdl():
            val = vdl_var.get().strip()
            self.settings.set("video_download_path", val)
        ctk.CTkButton(vdl_frame, image=save_emoji, text="", command=save_vdl, fg_color="#2a8cdb",width=70).pack(side="right", padx=0, pady=(0, 10))

        # Default Install Path for Programs
        inst_frame = ctk.CTkFrame(general_tab, fg_color="#232323", corner_radius=8)
        inst_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(inst_frame, text="Default Path for Installed Programs", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        inst_var = ctk.StringVar(value=self.settings.get("programs_install_path", ""))
        inst_entry = ctk.CTkEntry(inst_frame, textvariable=inst_var, width=400)
        inst_entry.pack(side="left", padx=(10, 5), pady=(0, 10))
        def browse_inst():
            path = filedialog.askdirectory(title="Select Install Directory")
            if path:
                inst_var.set(path)
        ctk.CTkButton(inst_frame, image=folder_emoji,text="", command=browse_inst, fg_color="#1f6aa5",width=70).pack(side="right", padx=10, pady=(0, 10))
        def save_inst():
            val = inst_var.get().strip()
            self.settings.set("programs_install_path", val)
        ctk.CTkButton(inst_frame, image=save_emoji, text="", command=save_inst, fg_color="#2a8cdb",width=70).pack(side="right", padx=0, pady=(0, 10))

        # Import/Export Settings
        imp_exp_frame = ctk.CTkFrame(general_tab, fg_color="#232323", corner_radius=8)
        imp_exp_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(imp_exp_frame, text="Import/Export Settings", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        def do_import():
            path = filedialog.askopenfilename(title="Import Settings", filetypes=[("JSON Files", "*.json"), ("All Files", "*")])
            if path:
                self.settings.import_settings(path)
                tk.messagebox.showinfo("Settings Imported", "Settings imported successfully. Please restart the app to apply changes.")
        def do_export():
            path = filedialog.asksaveasfilename(title="Export Settings", defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*")])
            if path:
                self.settings.export(path)
                tk.messagebox.showinfo("Settings Exported", "Settings exported successfully.")
        ctk.CTkButton(imp_exp_frame, text="Import", command=do_import, fg_color="#1f6aa5").pack(side="left", padx=10, pady=(0, 10))
        ctk.CTkButton(imp_exp_frame, text="Export", command=do_export, fg_color="#2a8cdb").pack(side="left", padx=10, pady=(0, 10))

        # --- Modules Tab ---
        modules_tab = self.tabs.add("Modules")
        modules_frame = ctk.CTkFrame(modules_tab, fg_color="#232323", corner_radius=8)
        modules_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(modules_frame, text="Modules", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        import importlib.util, glob
        module_files = glob.glob(os.path.join("modules", "*.py"))
        pyd_files = glob.glob(os.path.join("modules", "*.pyd"))
        module_files += pyd_files
        module_list = []
        for mod_path in module_files:
            mod_name = os.path.splitext(os.path.basename(mod_path))[0]
            if mod_name.startswith("__"):
                continue
            # For .pyd, skip if .py with same name already loaded
            if mod_path.endswith('.pyd') and os.path.exists(os.path.join("modules", f"{mod_name}.py")):
                continue
            spec = importlib.util.spec_from_file_location(mod_name, mod_path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                print(f"Failed to load module {mod_name}: {e}")
                continue
            mod_name_disp = getattr(mod, "module_name", mod_name)
            mod_desc = getattr(mod, "module_description", "")
            mod_version = getattr(mod, "module_version", "?")
            mod_icon = getattr(mod, "module_icon", None)
            mod_emoji = getattr(mod, "module_emoji", "🧩")
            # Remove spaces from emoji string
            if isinstance(mod_emoji, str):
                mod_emoji = mod_emoji.replace(" ", "")
            module_list.append({"name": mod_name_disp, "desc": mod_desc, "version": mod_version, "icon": mod_icon, "emoji": mod_emoji, "id": mod_name})
        module_list.sort(key=lambda m: m["name"].lower())
        for mod in module_list:
            row = ctk.CTkFrame(modules_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=4)
            icon_path = os.path.join("assets", mod["icon"]) if mod["icon"] and os.path.exists(os.path.join("assets", mod["icon"])) else None
            if icon_path:
                img = ctk.CTkImage(Image.open(icon_path), size=(32,32))
                icon = ctk.CTkLabel(row, image=img, text="")
            else:
                icon = ctk.CTkLabel(row, text=mod["emoji"], font=ctk.CTkFont(size=20))
            icon.pack(side="left", padx=(0,8))
            ctk.CTkLabel(row, text=mod["name"], font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0,8))
            ctk.CTkLabel(row, text=f"v{mod['version']}", font=ctk.CTkFont(size=11)).pack(side="left", padx=(0,8))
            ctk.CTkLabel(row, text=mod["desc"], font=ctk.CTkFont(size=11), text_color="#bbbbbb").pack(side="left", padx=(0,8))
            ctk.CTkButton(row, text="Uninstall", state="disabled",width=10, fg_color="#444444").pack(side="right", padx=4)
