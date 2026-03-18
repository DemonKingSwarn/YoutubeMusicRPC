# Youtube Music RPC

A simple terminal-based Discord Rich Presence client for YouTube Music.

## Features

- Displays currently playing track on Discord
- Shows album artwork, track title, and artist
- Displays playback state (playing/paused)
- Shows time remaining or elapsed
- Supports custom browser paths (AppImages, etc.)

## Requirements

- Python 3.10+
- Discord desktop app running
- Linux

## Installation

```bash
pip install -r requirements.txt
```

Or with uv:
```bash
uv pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Or with uv (recommended):
```bash
uv run python main.py
```

On first run, you'll be prompted to configure:
- Discord Client ID (or use default)
- Browser profile name
- Refresh rate
- Time display preference
- Custom browser path (for AppImages or non-standard browser locations)

Settings are stored in: `~/.config/ytmusic_rpc/settings.json`

Press `Ctrl+C` to stop.

## AppImage Browsers

If you're using a browser installed as an AppImage (e.g., Helium), select "yes" when asked for a custom browser path and enter the full path to the AppImage file.

## Notes

- Discord must be running for the presence to work
- The browser will be launched with remote debugging enabled
- Close all browser instances before starting if you encounter issues