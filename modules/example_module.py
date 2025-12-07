"""
Example Module Template for K Toolkit
-------------------------------------
To contribute a new module:
- Fill in the metadata below (name, emoji, etc.)
- Implement your UI as a CTkFrame subclass (see ExampleModuleUI)
- Use the provided setup_ui() pattern for layout
- Optionally, add a logic class for non-UI code
- Use docstrings and comments to help other contributors
"""
import yt_dlp as dlp
import customtkinter as ctk

# --- Import packages ---
# Ussualy you would import your module dependencies here.
# But since there are unlimited dependencies, its unreal to put that all in executable.
# So we use a dynamic import system that will try to import the module from the system pip.

try:
    import yt_dlp
except ImportError:
    from core.python_handler import try_import_with_system_pip
    yt_dlp = try_import_with_system_pip("yt_dlp", "yt_dlp")



# --- Module Metadata ---
module_version = "1.0.0"
module_name = "Example"
module_emoji = "👌"  # Emoji for the module (unicode or string)
module_icon = None   # Optional: path to an icon file
module_description = "Example module for demonstration purposes."

# --- Widget display info for home tab ---
home_widgets = {
    "show": True,
    "order": 1,  # Example order
    "desc": module_description,
}

# --- Settings for mod config tab ---
mod_settings = {
    "example_option": {
        "type": "bool",
        "default": True,
        "desc": "Enable example feature"
    }
}

class ExampleModuleUI(ctk.CTkFrame):
    """
    Example UI for a dynamic K Toolkit module.
    Inherit from CTkFrame and use setup_ui() for layout.
    """
    def __init__(self, parent, settings=None):
        super().__init__(parent, fg_color="transparent")
        self.settings = settings  # Optional: access global settings
        self.setup_ui()

    def setup_ui(self):
        """Create and layout widgets for the module UI."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        label = ctk.CTkLabel(self, text="Hello from Example Module!", font=ctk.CTkFont(size=18, weight="bold"))
        label.grid(row=0, column=0, padx=20, pady=20)
        # Add more widgets and logic here

    @staticmethod
    def home_widget(parent):
        frame = ctk.CTkFrame(parent, fg_color="#232323", corner_radius=8)
        ctk.CTkLabel(frame, text="Example Widget", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkLabel(frame, text="This is a sample widget from Example Module.", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=12, pady=(0, 6))
        return frame


# --- Widget display info and settings for module system ---
widget_display = home_widgets
settings_config = mod_settings

# For dynamic import system
ModuleUI = ExampleModuleUI