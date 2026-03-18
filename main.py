import json
import platform
import os
import sys
from src import App, Logger
from src.operating_systems.linux_operating_system import LinuxOperatingSystem
from src import __version__, __title__, __clientid___


def get_settings_path():
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "ytmusic_rpc")
    return os.path.join(config_dir, "settings.json")


def prepare_environment():
    settings_path = get_settings_path()
    settings_dir = os.path.dirname(settings_path)

    try:
        with open(settings_path, "r") as f:
            raw_settings = json.load(f)
    except FileNotFoundError:
        raw_settings = {"first_run": True}
    except json.decoder.JSONDecodeError:
        Logger.write(message="Invalid settings.json file.", level="ERROR")
        os.remove(settings_path)
        sys.exit(1)

    if raw_settings["first_run"] is True:
        os.makedirs(settings_dir, exist_ok=True)
        print(f"First run detected. Settings will be saved to {settings_path}")

        client_id = input("Use custom Discord Client ID? (yes/no): ")
        client_id = (
            __clientid___
            if client_id.lower() == "no"
            else input("Enter your Discord Client ID: ")
        )

        profile = (
            input("Browser profile name (press Enter for 'Default'): ") or "Default"
        )
        refresh_rate = input("Refresh rate in seconds (press Enter for 1): ")
        refresh_rate = int(refresh_rate) if refresh_rate.isdigit() else 1

        use_time_left = input("Display time remaining? (yes/no, default: yes): ")
        use_time_left = use_time_left.lower() != "no"

        browser_path = None
        custom = input("Use custom browser path (e.g., for AppImages)? (yes/no): ")
        if custom.lower() == "yes":
            browser_path = input("Enter full path to browser executable: ")

        raw_settings = {
            "first_run": False,
            "client_id": client_id,
            "profile_name": profile,
            "refresh_rate": refresh_rate,
            "display_time_left": use_time_left,
            "browser_path": browser_path,
        }
        with open(settings_path, "w") as f:
            json.dump(raw_settings, f, indent=2)
        Logger.write(message="Settings saved.")
        return raw_settings

    Logger.write(message=f"Settings loaded from {settings_path}")
    return raw_settings


if __name__ == "__main__":
    if platform.system() != "Linux":
        Logger.write(message="Sorry! This script only supports Linux.", level="ERROR")
        sys.exit(1)

    system = LinuxOperatingSystem()
    settings = prepare_environment()

    app = App(
        operating_system=system,
        client_id=settings["client_id"],
        version=__version__,
        title=__title__,
        profileName=settings["profile_name"],
        refreshRate=settings["refresh_rate"],
        useTimeLeft=settings["display_time_left"],
        browserPath=settings.get("browser_path"),
    )
    app.sync()

    try:
        app.run()
    except KeyboardInterrupt:
        Logger.write(message="User interrupted.")
        app.stop()
