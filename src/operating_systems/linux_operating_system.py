import os
import subprocess as sp
from .operating_system import OperatingSystem
from ..utils import find_browser_by_process, run_browser
from ..browsers import BROWSERS


class LinuxOperatingSystem(OperatingSystem):
    __slots__ = (
        "browser_process_name",
        "browser_executable_path",
        "browser_path",
    )

    def __init__(self):
        self.browser_path = None

    def get_default_browser(self) -> dict:
        default_browser_capture = sp.run(
            ["xdg-settings", "get", "default-web-browser"],
            capture_output=True,
            text=True,
        )
        if default_browser_capture.stderr != "":
            raise Exception("Can't find default browser")
        default_browser = default_browser_capture.stdout.strip().split(".")[0]
        found_browser = find_browser_by_process("linux", default_browser)
        if not found_browser:
            found_browser = BROWSERS[0].copy()
            found_browser["fullname"] = default_browser.capitalize()

        self.browser_process_name = found_browser.get("process", {}).get(
            "linux", default_browser
        )

        browser_path_capture = sp.run(
            ["which", default_browser], capture_output=True, text=True
        )
        if browser_path_capture.stderr != "":
            found_browser["path"] = ""
        else:
            found_browser["path"] = browser_path_capture.stdout.strip()
            self.browser_executable_path = browser_path_capture.stdout.strip()
        return found_browser

    def is_browser_running(self) -> bool:
        # If custom browser path is set, check for that specific process
        if self.browser_path:
            process_name = os.path.basename(self.browser_path)
            if process_name.endswith(".AppImage"):
                # For AppImages, check by full path
                all_processes = sp.run(
                    ["ps", "-e", "-o", "cmd"], capture_output=True, text=True
                )
                return self.browser_path in all_processes.stdout
            else:
                process_name = process_name
        else:
            process_name = self.browser_process_name
            if process_name == "google-chrome":
                process_name = "chrome"
        all_processes = sp.run(["ps", "-e"], capture_output=True)
        browser_processes = sp.run(
            ["grep", "-i", process_name],
            input=all_processes.stdout,
            capture_output=True,
        )
        filtered = sp.run(
            ["grep", "-v", "crashpad"],
            input=browser_processes.stdout,
            capture_output=True,
        ).stdout.decode()
        return filtered is not None and filtered != ""

    def run_browser_with_debugging_server(self, profile_name: str) -> None:
        user_home = os.path.expanduser("~")
        profile_path = os.path.join(user_home, ".config", "google-chrome", "Default")
        executable = self.browser_path or self.browser_executable_path
        run_browser(executable, profile_name, profile_path)

    def get_browser_process_name(self) -> str:
        return self.browser_process_name

    def set_browser_path(self, path: str) -> None:
        self.browser_path = path
