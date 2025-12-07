from core.UserInterface import UserInterface
from core.SettingsManager import SettingsManager

if __name__ == "__main__":
    settings = SettingsManager()
    app = UserInterface(settings)