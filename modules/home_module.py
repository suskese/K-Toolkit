import customtkinter as ctk
import psutil
import GPUtil
import platform
import os
import wmi
import threading
from PIL import Image

module_version = "1.0.0"
module_name = "Home"
module_emoji = "🏠"
module_icon = None
module_description = "Overview of your PC and quick access to modules."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True, 
    "order": 0,    
}

# --- Settings for mod config tab (none for home) ---
mod_settings = None

class HomeModuleUI(ctk.CTkFrame):
    def __init__(self, parent, settings=None, modules_info=None, customize_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings
        self.modules_info = modules_info or []
        self.customize_callback = customize_callback
        self._spec_labels = {}
        self._stop_update = False
        self._specs_lock = threading.Lock()
        self._latest_specs = self.get_specs()
        self.setup_ui()
        threading.Thread(target=self.update_specs_async, daemon=True).start()
        self.after(500, self.update_specs_ui)

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=0)  # PC Specs (fixed height)
        self.grid_rowconfigure(1, weight=1)  # Module Widgets (expand)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        # --- PC Specs and Storage in one row at the top ---
        self.specs_frame = ctk.CTkFrame(self, fg_color="#232323", corner_radius=8)
        self.specs_frame.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        self.specs_frame.grid_columnconfigure(0, weight=1)
        self.specs_frame.grid_columnconfigure(1, weight=1)
        # --- PC Specs (left) ---
        self.specs_left = ctk.CTkFrame(self.specs_frame, fg_color="transparent")
        self.specs_left.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)
        ctk.CTkLabel(self.specs_left, text="PC Specs", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        specs = self.get_specs()
        self._progress_bars = {}
        for label, value in specs.items():
            l = ctk.CTkLabel(self.specs_left, text=f"{label}: {value}", font=ctk.CTkFont(size=12))
            l.pack(anchor="w", padx=10)
            self._spec_labels[label] = l
            # Add progress bars for scalable things
            if label == "CPU":
                pb = ctk.CTkProgressBar(self.specs_left, width=220)
                pb.pack(anchor="w", padx=20, pady=(0, 6))
                self._progress_bars[label] = pb
            if label == "RAM":
                pb = ctk.CTkProgressBar(self.specs_left, width=220)
                pb.pack(anchor="w", padx=20, pady=(0, 6))
                self._progress_bars[label] = pb
            if label == "GPU":
                pb = ctk.CTkProgressBar(self.specs_left, width=220)
                pb.pack(anchor="w", padx=20, pady=(0, 6))
                self._progress_bars[label] = pb
        # --- Storage (right) ---
        self.specs_right = ctk.CTkFrame(self.specs_frame, fg_color="transparent")
        self.specs_right.grid(row=0, column=1, sticky="nsew", padx=(20, 0), pady=10)
        ctk.CTkLabel(self.specs_right, text="Storage", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self._storage_labels = {}
        self._storage_bars = {}
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except Exception:
                continue
            label = f"{part.device} ({part.mountpoint})"
            l = ctk.CTkLabel(self.specs_right, text=f"{label}: {usage.percent}% ({usage.used // (1024**3)}GB/{usage.total // (1024**3)}GB)", font=ctk.CTkFont(size=11))
            l.pack(anchor="w", padx=20)
            pb = ctk.CTkProgressBar(self.specs_right, width=220)
            pb.set(usage.percent / 100)
            pb.pack(anchor="w", padx=30, pady=(0, 6))
            self._storage_labels[label] = l
            self._storage_bars[label] = pb
        # --- Module Widgets Area (expand) ---
        # self.widgets_frame = ctk.CTkFrame(self, fg_color="#232323", corner_radius=8)
        # self.widgets_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")
        # self.widgets_frame.grid_rowconfigure(0, weight=1)
        # self.widgets_frame.grid_columnconfigure(0, weight=1)
        # ctk.CTkLabel(self.widgets_frame, text="Module Widgets", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(10, 2))
        # self.cards_container = ctk.CTkFrame(self.widgets_frame, fg_color="transparent")
        # self.cards_container.pack(fill="both", expand=True, padx=10, pady=10)
        # self.module_cards = {}
        # self.render_module_cards()
        # --- Customize Home Tab Button ---
        if self.customize_callback:
            ctk.CTkButton(self, text="Customize Home Tab", command=self.customize_callback, fg_color="#444444").grid(row=2, column=0, columnspan=2, pady=8)

    def render_module_cards(self):
        # Remove old cards
        for card in getattr(self, 'module_cards', {}).values():
            card.destroy()
        self.module_cards = {}
        # Get enabled/disabled state from settings
        enabled_dict = {}
        if self.settings and hasattr(self.settings, 'get'):
            enabled_dict = self.settings.get('home_widgets_enabled', {})
        for mod in self.modules_info:
            mod_id = mod.get('id') or mod.get('name')
            # Default: show if not explicitly disabled
            enabled = enabled_dict.get(mod_id, True)
            if not enabled:
                continue
            card = ctk.CTkFrame(self.cards_container, fg_color="#232323", corner_radius=12)
            card.pack(fill="x", padx=8, pady=8)
            # Card header
            ctk.CTkLabel(card, text=f"{mod.get('emoji','')} {mod.get('name','')}", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(card, text=mod.get('desc',''), font=ctk.CTkFont(size=11), text_color="#bbbbbb").pack(anchor="w", padx=16, pady=(0, 6))
            # If module provides a 'home_widget' function, call it to add custom content
            home_widget_func = mod.get('home_widget')
            if callable(home_widget_func):
                try:
                    widget = home_widget_func(card)
                    if widget:
                        widget.pack(fill="x", padx=16, pady=6)
                except Exception as e:
                    ctk.CTkLabel(card, text=f"Widget error: {e}", text_color="#ff5555").pack(anchor="w", padx=16, pady=6)
            self.module_cards[mod_id] = card

    def update_specs_async(self):
        while not self._stop_update:
            specs = self.get_specs(async_cpu=True)
            with self._specs_lock:
                self._latest_specs = specs
            threading.Event().wait(1)

    def update_specs_ui(self):
        with self._specs_lock:
            specs = self._latest_specs.copy()
        for label, value in specs.items():
            if label in self._spec_labels:
                self._spec_labels[label].configure(text=f"{label}: {value}")
            # Update progress bars
            if label == "CPU" and label in self._progress_bars:
                try:
                    percent = float(value.split("(")[-1].replace("%)", "").replace("%", "")) / 100
                except Exception:
                    percent = 0
                self._progress_bars[label].set(percent)
            if label == "RAM" and label in self._progress_bars:
                try:
                    percent = float(value.split("(")[-1].replace("%)", "").replace("%", "")) / 100
                except Exception:
                    percent = 0
                self._progress_bars[label].set(percent)
            if label == "GPU" and label in self._progress_bars:
                try:
                    percent = float(value.split("(")[-1].replace("%)", "").replace("%", "")) / 100
                except Exception:
                    percent = 0
                self._progress_bars[label].set(percent)
        # Update storage
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except Exception:
                continue
            label = f"{part.device} ({part.mountpoint})"
            if label in self._storage_labels:
                self._storage_labels[label].configure(text=f"{label}: {usage.percent}% ({usage.used // (1024**3)}GB/{usage.total // (1024**3)}GB)")
                self._storage_bars[label].set(usage.percent / 100)
        if not self._stop_update:
            self.after(500, self.update_specs_ui)

    def destroy(self):
        self._stop_update = True
        super().destroy()

    def get_specs(self, async_cpu=False):
        # CPU
        cpu_name = self.get_cpu_name()
        if async_cpu:
            cpu_usage = psutil.cpu_percent(interval=0.0)
        else:
            cpu_usage = psutil.cpu_percent(interval=None)
        # RAM
        ram = psutil.virtual_memory()
        ram_total = f"{ram.total // (1024**2)} MB"
        ram_used = f"{ram.used // (1024**2)} MB"
        # GPU
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_name = gpus[0].name
                gpu_load = f"{gpus[0].load*100:.1f}%"
            else:
                gpu_name = "None"
                gpu_load = "0%"
        except Exception:
            gpu_name = "Unknown"
            gpu_load = "?%"
        # OS
        os_name = platform.system() + " " + platform.release()
        return {
            "CPU": f"{cpu_name} ({cpu_usage}%)",
            "RAM": f"{ram_used} / {ram_total} ({ram.percent}%)",
            "GPU": f"{gpu_name} ({gpu_load})",
            "OS": os_name,
        }

    def get_cpu_name(self):
        try:
            if os.name == 'nt':
                c = wmi.WMI()
                for cpu in c.Win32_Processor():
                    return cpu.Name.strip()
            else:
                return platform.processor() or platform.uname().processor or "Unknown"
        except Exception:
            return platform.processor() or platform.uname().processor or "Unknown"

# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = HomeModuleUI
