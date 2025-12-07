import os
import json


import sys

def get_settings_file():
    # Store settings in %APPDATA%\KToolkit\toolbox_settings.json
    appdata = os.environ.get('APPDATA')
    base_path = os.path.join(appdata, 'KToolkit')
    os.makedirs(base_path, exist_ok=True)
    return os.path.join(base_path, 'toolbox_settings.json')

SETTINGS_FILE = get_settings_file()

DEFAULT_SETTINGS = {
    "ffmpeg_path": "",
    "video_download_path": "",
    "programs_install_path": "",
    "first_launch": True,
    "Dev mode": False
}

class SettingsManager:
    def __init__(self, settings_file=SETTINGS_FILE):
        self.settings_file = settings_file
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self.settings.update(json.load(f))
            except Exception:
                pass

    def save(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def export(self, export_path):
        with open(export_path, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def import_settings(self, import_path):
        with open(import_path, 'r') as f:
            self.settings.update(json.load(f))
        self.save()

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
