
import customtkinter as ctk
from core.ui_settings import SettingsTab
import tkinter as tk
from tkinter import messagebox
from core.SettingsManager import SettingsManager
from core.emoji import emoji_
import importlib.util
import glob
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class UserInterface:

    def show_blacklist_popup(self, violating, found):
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        msg = f"Violating program found please uninstall: {', '.join(violating)}"

        popup = tk.Toplevel()
        popup.title("Security Warning")
        tk.Label(popup, text=msg, fg="red", font=("Segoe UI", 12, "bold")).pack(padx=20, pady=(20,10))
        for prog in violating:
            tk.Label(popup, text=f"Detected: {prog}").pack(pady=2)
        import sys
        def close_and_exit():
            popup.destroy()
            sys.exit(0)
        tk.Button(popup, text="Close Toolbox", command=close_and_exit).pack(pady=(0, 20))
        popup.protocol("WM_DELETE_WINDOW", close_and_exit)
        popup.mainloop()
    def __init__(self, settings: SettingsManager):
        # --- Blacklist scan and pop-up before UI loads ---
        self.blacklist = [
            "Cheat Engine", "Roblox", "Roblox Studio", "Roblox Player",
        ]
        from core.program_detection import detect_programs_by_name, uninstall_program_by_registry_key
        found = detect_programs_by_name(self.blacklist)
        violating = [name for name, path in found.items() if path]
        if violating:
            self.show_blacklist_popup(violating, found)
            return

        self.settings = settings
        self.root = ctk.CTk()
        self.root.title("K Toolkit")
        icon_path = resource_path("assets/icon.ico")
        self.root.iconbitmap(icon_path)
        self.root.resizable(False, False)
        self.root.minsize(950, 610)
        self.root.geometry("950x610")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        ctk.CTkFont(ctk.CTkFont(family="Segoe UI", size=13))

        # --- Main Layout: Sidebar + Main Content ---
        self.root.grid_columnconfigure(0, weight=0)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self.root, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(99, weight=1)  # Pushes author label to bottom

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="K Toolkit", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),wraplength=100)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        row = 1
        self.settings_button = ctk.CTkButton(self.sidebar_frame,
                                             image=emoji_("     ⚙️"),
                                             text="Settings",
                                             command=lambda: self.show_tab("settings"),
                                             fg_color="transparent", hover_color="#2a8cdb", anchor="w",
                                             font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                                             text_color_disabled="#606060")
        self.settings_button.grid(row=999, column=0, sticky="ew", padx=20, pady=20)  # Always at very bottom
        # No row weight for 999, so settings stays at the bottom
        self.sidebar_frame.grid_rowconfigure(999, weight=0)  # Pushes settings button to bottom

        # --- Main Content (Tabbed) ---
        self.main_content_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="#2b2b2b")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew")
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # --- Tabs ---
        self.settings_ui = SettingsTab(self.main_content_frame, self.settings)
        self.frames = {
            "settings": self.settings_ui,
        }


        # --- Dynamic Module Discovery ---
        self.module_frames = {}
        self.module_info = []
        self.module_buttons = []
        self.module_button_map = {}
        row = 2  # After built-in buttons


        # Load regular modules (.py) and compiled modules (.pyd) from 'modules' folder
        module_files = glob.glob(os.path.join("modules", "*.py"))
        pyd_files = glob.glob(os.path.join("modules", "*.pyd"))
        all_module_files = module_files + pyd_files
        for mod_path in all_module_files:
            mod_name = os.path.splitext(os.path.basename(mod_path))[0]
            if mod_name.startswith("__") or mod_name == "example_module":
                continue
            # Load .py modules as before
            if mod_path.endswith('.py'):
                spec = importlib.util.spec_from_file_location(mod_name, mod_path)
                mod = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(mod)
                except Exception as e:
                    print(f"Failed to load module {mod_name}: {e}")
                    continue
            # Load .pyd modules using importlib
            elif mod_path.endswith('.pyd'):
                modules_dir = os.path.abspath(os.path.dirname(mod_path))
                if modules_dir not in sys.path:
                    sys.path.insert(0, modules_dir)
                try:
                    mod = importlib.import_module(mod_name)
                except Exception as e:
                    print(f"Failed to load compiled module {mod_name}: {e}")
                    continue
            else:
                continue
            ui_class = None
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, type) and issubclass(obj, ctk.CTkFrame) and obj is not ctk.CTkFrame:
                    ui_class = obj
                    break
            if not ui_class:
                continue
            mod_emoji = getattr(mod, "module_emoji", "🧩")
            mod_name_disp = getattr(mod, "module_name", mod_name)
            mod_desc = getattr(mod, "module_description", "")
            mod_id = mod_name
            home_widget_func = getattr(mod, "home_widget", None)
            btn = ctk.CTkButton(self.sidebar_frame, image=emoji_(mod_emoji), text=mod_name_disp, command=lambda n=mod_name: self.show_tab(n), fg_color="transparent", hover_color="#2a8cdb", anchor="w", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color_disabled="#606060")
            btn.grid(row=row, column=0, sticky="ew", padx=20, pady=5)
            self.module_buttons.append((btn, mod_name))
            self.module_button_map[mod_name] = btn
            mod_info = {"name": mod_name_disp, "desc": mod_desc, "emoji": mod_emoji, "id": mod_id, "home_widget": home_widget_func}
            if mod_name == "home_module":
                frame = ui_class(self.main_content_frame, self.settings, modules_info=self.module_info)
            else:
                try:
                    frame = ui_class(self.main_content_frame, self.settings)
                except TypeError:
                    frame = ui_class(self.main_content_frame)
            self.module_frames[mod_name] = frame
            mod_info["frame"] = frame
            self.module_info.append(mod_info)
            self.frames[mod_name] = frame
            row += 1

        # --- Dev mode: Load dll_converter and pyinstaller_compiler from core if enabled ---
        if self.settings.get("Dev mode", False):
            for dev_mod in ["dll_converter", "nuitka"]:
                dev_path = os.path.join("core", f"{dev_mod}.py")
                if os.path.exists(dev_path):
                    mod_name = dev_mod
                    spec = importlib.util.spec_from_file_location(mod_name, dev_path)
                    mod = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(mod)
                    except Exception as e:
                        print(f"Failed to load core module {mod_name}: {e}")
                    else:
                        ui_class = getattr(mod, "ModuleUI", None)
                        if ui_class and issubclass(ui_class, ctk.CTkFrame):
                            mod_emoji = getattr(mod, "module_emoji", "🧩")
                            mod_name_disp = getattr(mod, "module_name", mod_name)
                            mod_desc = getattr(mod, "module_description", "")
                            mod_id = mod_name
                            home_widget_func = getattr(mod, "home_widget", None)
                            btn = ctk.CTkButton(self.sidebar_frame, image=emoji_(mod_emoji), text=mod_name_disp, command=lambda n=mod_name: self.show_tab(n), fg_color="transparent", hover_color="#2a8cdb", anchor="w", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color_disabled="#606060")
                            btn.grid(row=row, column=0, sticky="ew", padx=20, pady=5)
                            self.module_buttons.append((btn, mod_name))
                            self.module_button_map[mod_name] = btn
                            mod_info = {"name": mod_name_disp, "desc": mod_desc, "emoji": mod_emoji, "id": mod_id, "home_widget": home_widget_func}
                            frame = ui_class(self.main_content_frame, self.settings)
                            self.module_frames[mod_name] = frame
                            mod_info["frame"] = frame
                            self.module_info.append(mod_info)
                            self.frames[mod_name] = frame
                            row += 1

        self.author_label = ctk.CTkLabel(self.sidebar_frame, text="By MisterK", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color="#808080")
        self.author_label.grid(row=998, column=0, padx=20, pady=(10, 10), sticky="s")
        self.sidebar_frame.grid_rowconfigure(998, weight=1)  # Pushes author label to just above settings

        # --- First Launch FFmpeg Check ---
        if self.settings.get("first_launch", True):
            self.handle_first_launch_ffmpeg_check()

        self.current_tab = None
        self.show_tab("home_module")
        self.root.mainloop()

    def handle_first_launch_ffmpeg_check(self):
        import shutil
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            self.settings.set("ffmpeg_path", "PATH")
        else:
            # Show custom CTk dialog for missing FFmpeg
            def add_to_path(bin_path):
                import sys
                import os
                import ctypes
                import tkinter as tk
                import winreg

                def is_admin():
                    try:
                        return ctypes.windll.shell32.IsUserAnAdmin() != 0
                    except Exception:
                        return False

                def broadcast_env_change():
                    import ctypes
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x001A
                    SMTO_ABORTIFHUNG = 0x0002
                    result = ctypes.c_long()
                    ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                        "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
                    )

                def update_system_path(bin_path):
                    # Read current system PATH
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                        path_value, _ = winreg.QueryValueEx(key, "Path")
                        paths = path_value.split(";")
                        if bin_path not in paths:
                            new_path = path_value + (";" if not path_value.endswith(";") else "") + bin_path
                            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                            broadcast_env_change()
                            return True
                        else:
                            return False

                if not is_admin():
                    # Relaunch as admin
                    try:
                        params = f'"{sys.argv[0]}" --add-ffmpeg-path="{bin_path}"'
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                    except Exception as e:
                        tk.messagebox.showerror("Error", f"Failed to request admin privileges: {e}")
                    return

                # If admin, update PATH
                try:
                    changed = update_system_path(bin_path)
                    if changed:
                        tk.messagebox.showinfo("Done", f"Added {bin_path} to system PATH. Please restart your PC or log out and back in for changes to take effect.")
                    else:
                        tk.messagebox.showinfo("Info", f"{bin_path} is already in the system PATH.")
                except Exception as e:
                    tk.messagebox.showerror("Error", f"Failed to add to PATH: {e}")

            def open_install_tab():
                self.show_tab("installing")

            dialog = ctk.CTkToplevel(self.root)
            dialog.title("FFmpeg Not Found")
            dialog.geometry("420x260")
            dialog.resizable(False, False)
            dialog.grab_set()
            ctk.CTkLabel(dialog, text="FFmpeg was not found on your system.", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 8))
            ctk.CTkLabel(dialog, text="You need FFmpeg for video downloading.", font=ctk.CTkFont(size=13)).pack(pady=(0, 8))
            ctk.CTkLabel(dialog, text="What would you like to do?", font=ctk.CTkFont(size=13)).pack(pady=(0, 10))

            def try_add_path():
                # Ask user for ffmpeg bin folder
                from tkinter import filedialog as fd
                bin_path = fd.askdirectory(title="Select FFmpeg bin Folder (should contain ffmpeg.exe)")
                if bin_path and os.path.exists(os.path.join(bin_path, "ffmpeg.exe")):
                    add_to_path(bin_path)
                    tk.messagebox.showinfo("Done", f"Added {bin_path} to system PATH. Please restart your PC or log out and back in for changes to take effect.")
                    dialog.destroy()
                else:
                    tk.messagebox.showerror("Not Found", "ffmpeg.exe not found in selected folder.")

            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=10)
            ctk.CTkButton(btn_frame, text="Install FFmpeg (Toolbox)", command=lambda: [dialog.destroy(), open_install_tab()], fg_color="#2a8cdb").pack(side="left", padx=8)
            ctk.CTkButton(btn_frame, text="Add FFmpeg to PATH", command=try_add_path, fg_color="#1f6aa5").pack(side="left", padx=8)
            ctk.CTkButton(btn_frame, text="Close", command=dialog.destroy, fg_color="#444444").pack(side="left", padx=8)

            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.wait_window()
        self.settings.set("first_launch", False)

    def show_tab(self, name):
        if self.current_tab:
            self.current_tab.grid_remove()
        frame = self.frames.get(name)
        if frame:
            frame.grid(row=0, column=0, sticky="nsew")
            self.current_tab = frame
            self.update_navigation_buttons(name)
            # --- Highlight module buttons if needed ---
            for btn, mod_name in self.module_buttons:
                if name == mod_name:
                    btn.configure(fg_color="#1f6aa5", text_color="white", text_color_disabled="white")
                else:
                    btn.configure(fg_color="transparent", text_color="white", text_color_disabled="#606060")
        else:
            print(f"Error: Tab '{name}' not found.")

    def update_navigation_buttons(self, active_tab):
        for button, tab in [
            (self.settings_button, "settings"),
        ]:
            if active_tab == tab:
                button.configure(fg_color="#1f6aa5", text_color="white", text_color_disabled="white")
            else:
                button.configure(fg_color="transparent", text_color="white", text_color_disabled="#606060")
        # Also update module buttons
        for btn, mod_name in self.module_buttons:
            if active_tab == mod_name:
                btn.configure(fg_color="#1f6aa5", text_color="white", text_color_disabled="white")
            else:
                btn.configure(fg_color="transparent", text_color="white", text_color_disabled="#606060")
