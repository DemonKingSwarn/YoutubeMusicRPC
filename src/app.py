import time
import os
from .presence import Presence
from .logger import Logger
from .tab import Tab
from .operating_systems.operating_system import OperatingSystem
from .utils import (
    remote_debugging,
    get_browser_tabs,
)

DISCORD_STATUS_LIMIT = 15


class App:
    """Core class of the application."""

    __slots__ = (
        "__presence",
        "__browser",
        "last_tab",
        "connected",
        "version",
        "title",
        "__profileName",
        "refreshRate",
        "useTimeLeft",
        "__operating_system",
        "__browserPath",
    )

    def __init__(
        self,
        operating_system: OperatingSystem,
        client_id: str,
        version: str,
        title: str,
        profileName: str = "Default",
        refreshRate: int = 1,
        useTimeLeft: bool = True,
        browserPath: str = None,
    ):
        Logger.write(message=f"{title} v{version}", level="INFO")
        Logger.write(message="initialized, to stop, press CTRL+C.")
        self.__presence = Presence(client_id=client_id)
        self.version = version
        self.title = title
        self.last_tab = None
        self.connected = False
        self.__browser = None
        self.refreshRate = refreshRate
        self.useTimeLeft = useTimeLeft
        self.__profileName = profileName
        self.__operating_system = operating_system
        self.__browserPath = browserPath

    def __handle_exception(self, exc: Exception) -> None:
        Logger.write(message=str(exc), level="ERROR", origin=self)

    def sync(self) -> None:
        Logger.write(message="syncing..")
        try:
            status = self.__presence.connect()
            if not status:
                raise Exception("Can't connect to Discord.")
            if self.__browserPath:
                import os

                if not os.path.exists(self.__browserPath):
                    raise Exception(f"Browser path not found: {self.__browserPath}")
                self.__browser = {
                    "fullname": os.path.basename(self.__browserPath),
                    "path": self.__browserPath,
                }
                self.__operating_system.browser_path = self.__browserPath
                self.__operating_system.browser_executable_path = self.__browserPath
                self.__operating_system.browser_process_name = os.path.basename(
                    self.__browserPath
                )
            else:
                self.__browser = self.__operating_system.get_default_browser()
                if not self.__browser:
                    raise Exception("Can't find default browser in your system.")
            self.connected = True
            Logger.write(
                message=f"Browser: {self.__browser.get('fullname', 'Unknown')}"
            )
        except Exception as exc:
            self.__handle_exception(exc)

    def stop(self) -> None:
        if self.connected:
            self.connected = False
            self.__presence.close()
            Logger.write(message="stopped.")

    def update_tabs(self) -> list:
        tabs = []
        tab_list = get_browser_tabs(filter_url="music.youtube.com")
        if tab_list:
            for tab_data in tab_list:
                tab = Tab(**tab_data)
                tab.update()
                tabs.append(tab)
        return tabs

    def run(self) -> None:
        last_updated_time: int = 1
        try:
            if not self.connected:
                raise RuntimeError("Not connected.")
            browser_running = self.__operating_system.is_browser_running()
            if not remote_debugging() and browser_running:
                Logger.write(
                    message=f"Detected browser running ({self.__operating_system.get_browser_process_name()}) without remote debugging enabled.",
                    level="WARNING",
                )
                raise RuntimeError("Please close all browser instances and try again.")
            if not remote_debugging():
                Logger.write(
                    message="Remote debugging is not enabled, starting browser..",
                    level="WARNING",
                )
                self.__operating_system.run_browser_with_debugging_server(
                    self.__profileName
                )
            else:
                Logger.write(
                    message="Remote debugging is enabled, connected successfully."
                )
            Logger.write(message="synced and connected.")
            Logger.write(message="Starting presence loop..")
            time.sleep(3)
            while self.connected:
                silent = False
                update_unix_time: float = time.time()
                tabs = self.update_tabs()
                tab = [tab for tab in tabs if tab.playing] or [
                    tab for tab in tabs if tab.pause
                ]
                if not tab:
                    Logger.write(message="No tab found.")
                    self.__presence.update(
                        details="No activity",
                        large_image="logo",
                        small_image="pause",
                        small_text=self.__browser["fullname"],
                        buttons=[
                            {
                                "label": "Download App",
                                "url": "https://manucabral.github.io/YoutubeMusicRPC/",
                            },
                        ],
                    )
                    time.sleep(DISCORD_STATUS_LIMIT)
                    continue
                tab = tab[0]
                if tab.ad:
                    Logger.write(message="Ad detected.")
                    time.sleep(DISCORD_STATUS_LIMIT)
                    continue

                if self.last_tab and self.last_tab == tab:
                    delta_estimated_end_times = abs(
                        self.last_tab.projected_end_time - tab.projected_end_time
                    )
                    playstate_manually_adjusted = delta_estimated_end_times > 1
                    silent = (
                        self.last_tab.projected_end_time + self.refreshRate
                        < update_unix_time
                        or playstate_manually_adjusted
                    )
                    if (
                        tab.title == self.last_tab.title
                        and tab.artist == self.last_tab.artist
                        and tab.projected_end_time + self.refreshRate > update_unix_time
                        and not playstate_manually_adjusted
                        and not tab.pause
                    ):
                        time.sleep(self.refreshRate)
                        continue

                if tab.pause:
                    silent = True

                if self.last_tab and self.last_tab.start_time == tab.start_time:
                    time.sleep(self.refreshRate)
                    continue

                if last_updated_time + 15 > update_unix_time:
                    remaining = update_unix_time - (last_updated_time + 15)
                    if remaining < 0:
                        remaining = 1
                    time.sleep(remaining)
                    continue
                last_updated_time = int(update_unix_time)
                self.last_tab = tab

                Logger.write(
                    message=f"Playing {self.last_tab.title} by {self.last_tab.artist}",
                    silent=silent,
                )

                self.__presence.update(
                    silent=silent,
                    details=self.last_tab.title,
                    state=self.last_tab.artist,
                    large_image=self.last_tab.artwork,
                    large_text=f"{self.title} v{self.version}",
                    small_image="pause" if self.last_tab.pause else "play",
                    small_text=self.__browser["fullname"],
                    buttons=[
                        {"label": "Listen In Youtube Music", "url": self.last_tab.url},
                        {
                            "label": "Download App",
                            "url": "https://manucabral.github.io/YoutubeMusicRPC/",
                        },
                    ],
                    start=self.last_tab.start_time,
                    end=self.last_tab.projected_end_time + self.refreshRate
                    if self.useTimeLeft
                    else None,
                )
        except Exception as exc:
            self.__handle_exception(exc)
            if exc.__class__.__name__ == "URLError":
                Logger.write(
                    message="Please close all browser instances and try again. Also, close Youtube Music Desktop App if you are using it.",
                    level="WARN",
                )
