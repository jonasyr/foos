# AGENTS.MD: AI Collaboration Guide for Foos

**Last Updated:** November 2025  
**Hardware:** Raspberry Pi 4 Model B Rev 1.1  
**OS:** Debian GNU/Linux 13 (trixie)  
**Python:** 3.13.5  
**Branch:** feature/button-controls

This document provides essential context for AI models interacting with this project. It includes critical local system configurations and deployment details discovered during development.

## 1. Project Overview & Purpose

* **Primary Goal:** Event-driven foosball scorekeeping and instant replay system that runs on a Raspberry Pi 4, capturing goals, managing replays, integrating with tournament/league services, and providing a kiosk-style 3D UI with hardware button control.
* **Business Domain:** Embedded multimedia application for recreational foosball tables combining hardware sensors (buttons, Arduino goal detectors), live Pi3D graphics, camera-based instant replay, and LAN-based tournament sync.
* **Current Deployment:** Raspberry Pi 4 Model B connected to local network (192.168.178.165), integrates with foos-tournament web service running on port 4567.

## 2. Core Technologies & Stack

* **Languages:** Python 3.13.5 (primary application logic), C (Raspberry Pi OpenMAX replay player), Bash (setup & maintenance scripts), Arduino sketches for peripheral hardware.
* **Frameworks & Runtimes:** 
  * Pi3D for OpenGL ES 3D-rendered UI (2560x1440@25fps)
  * Python threading/multiprocessing for event bus and plugin isolation
  * libcamera v0.5.2 for OV5647 camera module capture
  * Raspberry Pi GPU (VideoCore) for hardware-accelerated video playback
  * pygame 2.6.1 for input handling
* **Databases:** Local JSON files (`league.json`, result files in `league/results/`). Syncs with foos-tournament SQLite database via HTTP API.
* **Key Libraries/Dependencies:** 
  * Pi3D, NumPy, Pillow (image handling)
  * requests (HTTP API client for league sync)
  * RPi.GPIO / rpi-lgpio (BCM GPIO pin control)
  * libcamera-apps (camera capture to H.264)
  * ffmpeg/avconv (video processing)
  * evdev, inotify_simple (optional input methods)
  * google-api-python-client (optional YouTube uploads)
  * Slack/HipChat clients (optional notifications)
* **Platforms:** Raspberry Pi 4 Model B (tested), Pi 2/3 compatible. X11 desktop support for debugging with `-s` scale flag.
* **Package Manager:** `pip3` with `requirements.txt`; system packages via apt; C component builds via `make` in `video/player`.

## 3. Architectural Patterns

* **Overall Architecture:** Monolithic event-driven application with a plugin architecture. A central message bus (`foos.bus.Bus`) fans events to plugins that encapsulate individual features (scorekeeping, camera, uploads, league sync, hardware IO).
* **Directory Structure Philosophy:**
  * `/foos`: Core Python package - `foos.py` (entrypoint), `bus.py` (event bus), `config.py` (overrides), `config_getter.py`, `platform.py`, `plugin_handler.py`, `process.py`, `clock.py`, `utils.py`
  * `/foos/ui`: Pi3D GUI implementation (`ui.py`, `anim.py`, components)
  * `/plugins`: Feature modules exposing `Plugin` classes that subscribe to bus events:
    * **Core:** `score.py`, `game.py`, `menu.py`, `control.py`
    * **I/O:** `io_raspberry.py` (GPIO buttons - pins 5, 17, 23, 25, 27), `io_keyboard.py`, `io_debug.py`, `buttons.py` (new 5-button handler with long-press on pin 5)
    * **Media:** `camera.py`, `replay.py`, `replay_bridge.py`, `sound.py`
    * **League:** `league.py`, `league_sync.py`, `stats_event_logger.py` (NEW - goal-by-goal tracking for official matches)
    * **Optional:** `bot.py`, `slackbot.py`, `hipbot.py`, `upload.py`, `arduino.py`, `leds.py`, `motiondetector.py`, `standby.py`
  * `/video`: Replay scripts (`run-camera.sh`, `replay.sh`, `generate-replay.sh`) and C OpenMAX player (`player/`)
  * `/league`: Match data directory (`league.json` for match list, `results/` for completed matches, `processed/` for synced results)
  * `/arduino`: Goal detector firmware and schematics
  * `/doc`: Installation, hardware setup, UI guide, troubleshooting
  * `/debug`: Event simulation scripts for testing without hardware
  * `/tools`: Developer utilities (`detect_movement.py`, `test_stats_integration.py`, `verify_stats_setup.sh`)
  * `/img`, `/sounds`: UI assets (backgrounds, icons, numbers, audio files)
  * Root scripts: `check` (environment validation), `boot.sh`, `main.sh`, `foos.sh` (daemon startup), `setup-trixie.sh` (Debian 13 installer)
* **Module Organization:** Core modules under `foos/` package, UI under `foos/ui/`, plugins as flat modules in `/plugins/`. Feature activation controlled by `config.py` overriding `config_base.py` defaults (`plugins` set, GPIO pin mappings, league URL/API key).

## 4. Coding Conventions & Style Guide

* **Formatting:** Python code follows standard PEP 8-aligned formatting—4-space indentation, blank lines between class/method definitions, trailing commas avoided unless needed. C code in `video/player` keeps upstream formatting; shell scripts prefer POSIX sh or bash with defensive flags (`set -euo pipefail`).
* **Naming Conventions:**
  * Python modules: lowercase with underscores (`plugin_handler.py`).
  * Classes: PascalCase (`Bus`, `Plugin`, `Gui`).
  * Functions/procedures and variables: snake_case (`check_win`, `last_goal_clock`).
  * Constants/config entries: snake_case or lowercase keys inside dicts (`game_modes`, `hipchat_token`).
  * Event names on the bus are lower_snake_case strings (`score_changed`, `menu_show`).
* **API Design:**
  * **Style:** Procedural/OO hybrid. Plugins encapsulate state in classes but interact via procedural message passing over the bus.
  * **Abstraction:** `Bus` abstracts event delivery, while `PluginHandler` handles discovery/instantiation. UI exposes registries (e.g., `registerMenu`) for plugins to contribute components without direct coupling.
  * **Extensibility:** New functionality is added by defining additional plugins that subscribe to relevant events and optionally emit new ones. Config flags (`config.plugins`) control activation.
  * **Trade-offs:** Prioritizes responsiveness and hardware integration over strict safety. Threads and multiprocessing queues are used for isolation, while logging captures failure modes instead of raising.
* **Common Patterns & Idioms:**
  * **Metaprogramming:** Limited to Python dynamic imports of plugins (`importlib.import_module`). No heavy template/macro usage.
  * **Memory Management:** Relies on Python’s GC and high-level collections. C replay player manually manages buffers per OpenMAX examples.
  * **Polymorphism:** Achieved via duck typing; all plugins expose a `Plugin` class with consistent lifecycle. IO plugins inherit from `IOBase` to share threaded reader/writer patterns.
  * **Type Safety:** Informal—runtime checks and logging provide safeguards (e.g., ignoring too-frequent goals).
  * **Concurrency:** Extensive use of Python `threading.Thread` for background tasks (event subscribers, IO loops) and `multiprocessing.Queue` for inter-thread event dispatch. Some plugins also spawn daemon threads for continuous polling.
* **Error Handling:** Emphasizes logging via the configured logging dict. Exceptions are caught around IO boundaries to prevent plugin threads from crashing, and unexpected conditions emit warnings/errors instead of raising to the main loop.

## 5. Key Files & Entrypoints

* **Main Entrypoint:** `foos.py` (invoked via `./foos.py` or `./foos.sh`); it sets up logging, command-line scaling/framerate options, initializes the event bus, loads plugins, and launches the Pi3D GUI loop.
* **Configuration:**
  * `config_base.py` defines defaults (plugins, video settings, logging).
  * `config.py.sample` demonstrates overrides; copy to `config.py` for local customization.
  * `client_secrets.json.sample`, `league.json.sample` provide service-specific placeholders.
* **CI/CD Pipeline:** No CI definitions are present. Builds and checks are manual.

## 6. Development & Testing Workflow

* **Local Development Environment:**
  1. Install system dependencies per `doc/Installation.md` or the automated `setup-trixie.sh` (Debian/Raspberry Pi OS) script—ensures ffmpeg, gpio tools, tmpfs setup, and Python packages.
  2. Copy `config.py.sample` to `config.py` and adjust plugins, GPIO pins, and secrets as needed.
  3. (Optional) Build the replay player with `make` inside `video/player` to obtain the `player` binary required by the replay scripts.
  4. Run `./check` to validate environment prerequisites; follow its prompts for missing binaries or GPU memory adjustments.
  5. Launch the application with `python3 foos.py` (use `-s` to scale UI under X11).
* **Task Configuration:** There are no Nimble or `.nims` tasks. Python scripts and shell utilities are executed directly.
* **Testing:** No automated unit test suite is provided. Use the `debug/` shell scripts and mock plugins to simulate button presses and goal events for manual verification. Ensure new features integrate with the bus without regressing existing plugins.
* **CI/CD Process:** Manual; contributors are expected to run `./check`, rebuild `video/player` when touching C code, and test the UI on target hardware or X11 before committing.

## 7. Critical Local Configuration & Deployment Notes

**IMPORTANT: These are real-world deployment settings and fixes required on the actual Raspberry Pi system.**

### Hardware Configuration
* **Raspberry Pi 4 Model B Rev 1.1** running Debian GNU/Linux 13 (trixie)
* **Display:** 2560x1440 @ 25fps (configured in `config.py`)
* **Camera:** OV5647 module via libcamera (CSI ribbon cable)
* **GPIO Buttons (BCM numbering):**
  * Pin 17: yellow_plus (score +1 for yellow team)
  * Pin 23: yellow_minus (score -1 for yellow team)
  * Pin 27: black_plus (score +1 for black team)
  * Pin 25: black_minus (score -1 for black team)
  * Pin 5: OK button (short press = menu OK, **long press = instant replay**, debounce 600ms)
* **Network:** Static/DHCP at 192.168.178.165, hostname `foosball-pi`

### Required System Packages (Debian 13/trixie)
```bash
sudo apt-get install python3 python3-pip python3-pil python3-numpy \
  libcamera-apps ffmpeg sox sqlite3 git \
  libgles2-mesa-dev libegl1-mesa-dev
```

### Python Environment Setup
```bash
cd /home/pi/foos-project/foos
pip3 install -r requirements.txt
# Key packages: pi3d, pygame, RPi.GPIO/rpi-lgpio, requests, pillow
```

### Camera Configuration
* Uses libcamera v0.5.2 with tuning file `/usr/share/libcamera/ipa/rpi/vc4/ov5647.json`
* Camera capture runs in background via `video/run-camera.sh` (writes chunks to `/dev/shm/replay`)
* **Important:** tmpfs must be mounted at `/dev/shm` for replay buffer (configured in `setup-trixie.sh`)

### League Integration Configuration (`config.py`)
```python
league_url = 'http://192.168.178.165:4567/api'  # foos-tournament on same Pi
league_apikey = 'change-me-supersecret'  # Must match foos-tournament config.yaml
league_season = 'Season 2025'  # Must exist in foos-tournament database
league_stats_api = False  # Set True when stats API fully implemented
```

### Game Mode Configuration
* **League matches play to 10 goals** (configured in `config_base.py` line 23 and `league.py` lines 115, 122)
* Game modes: `[(None, None), (3, None), (5, None), (10, None), (3, 120)]`
  * Mode index 3 = 10 goals (used for league/tournament matches)
  * Mode index 2 = 5 goals (free play)
  * Mode index 1 = 3 goals (quick play)

### Known Issues & Fixes Applied

#### 1. Button Long-Press for Instant Replay
* **Issue:** OK button (pin 5) previously only worked for menu navigation
* **Fix:** Modified `plugins/buttons.py` to detect long press (>0.5s hold) and trigger `instant_replay` event
* **Behavior:** Short press = menu OK, Long press = replay last goal

#### 2. Stats Event Logger Plugin
* **Purpose:** Track goal-by-goal timeline ONLY for official tournament matches (ignores free play)
* **Location:** `plugins/stats_event_logger.py`
* **Activation:** Subscribes to `start_competition` (not `menu_show`!) to avoid logging free play
* **Data Collected:** Team scores per goal, timestamps, player IDs from league match data
* **Upload:** Optional POST to foos-tournament `/api/matches/:id/goals` (when `league_stats_api=True`)
* **Important:** Match must have ID from foos-tournament database to be tracked

#### 3. League Match Result Format
* **Current Format:** Single submatch with one score pair `[yellow_score, black_score]`
* **Example:** `{"id": 1002, "results": [[4, 10]], "start": 1762209376, "end": 1762209451}`
* **Known Limitation:** foos-tournament `result_processor.rb` expects 3 submatches (not implemented yet)
* **Workaround:** Results written to `league/results/result_XXXX.json` but must be manually imported

#### 4. League Directory Structure
* **Must exist:** `/home/pi/foos-project/foos/league/` with subdirectories:
  * `league.json` - match list from foos-tournament
  * `results/` - completed match results (auto-created)
  * `processed/` - synced results (auto-created)

### Running the Application

```bash
# Start from project root
cd /home/pi/foos-project/foos

# Check environment prerequisites
./check

# Run in foreground (for debugging)
python3 foos.py

# Run with UI scaling on desktop (X11)
python3 foos.py -s

# Background daemon mode
./foos.sh start
./foos.sh stop
./foos.sh restart
```

### Integration with foos-tournament
* **Requires:** foos-tournament running on http://192.168.178.165:4567
* **API Key:** Must match in both `foos/config.py` and `foos-tournament/config.yaml`
* **Match Sync:**
  * `league_sync.py` polls `/api/get_open_matches` and posts results to `/api/set_result`
  * `stats_event_logger.py` (NEW) tracks goal timeline for analytics
* **Match Creation:** Matches must exist in foos-tournament database AND `league.json` file
* **See:** foos-tournament AGENTS.md for database schema and setup details

## 8. Specific Instructions for AI Collaboration

* **Contribution Guidelines:**
  * Follow the plugin-based architecture—prefer adding new capabilities as plugins or extensions of existing ones rather than hard-coding into the core GUI.
  * Maintain thread safety when subscribing to the bus; use the provided `thread=True` flag for long-running handlers and respect queue backpressure.
  * Extend configuration via overrides in `config.py`; do not modify `config_base.py` defaults unless changing project-wide behavior.
  * When altering UI assets, keep resources under `/img` and reference them via `foos/ui/ui.py` helpers (`load_texture`, `img`).
* **Security:** Never hardcode production secrets. Use sample files for tokens (`client_secrets.json.sample`, `config.py.sample`) and document any required environment variables. Be mindful of subprocess calls (`foos/process.py`) and validate/escape inputs when integrating new commands.
* **Dependencies:** Add Python packages to `requirements.txt` and note Raspberry Pi system packages in documentation or `setup-trixie.sh`. For C or shell dependencies, update `video/player/Makefile` or the relevant scripts. Run `pip3 install -r requirements.txt` locally to confirm compatibility.
* **Commit Messages:** Existing history favors descriptive, sentence-style messages summarizing refactors. Keep messages clear about the scope (e.g., “Refactor button handling…”). Conventional Commit prefixes are not currently enforced, but concise summaries are appreciated.


* **Event Bus Patterns:**
  * Use `bus.subscribe_map({'event_name': handler_method}, thread=True)` for multiple events
  * Common events: `score_changed`, `goal_event`, `win_game`, `start_competition`, `cancel_competition`, `menu_show`, `menu_hide`, `instant_replay`, `set_game_mode`, `reset_score`
  * Emit events with `bus.notify('event_name', data_dict)`
* **GPIO Safety:** Always use BCM pin numbering. Verify pin availability with `./check` before modifying `config.py` pin mappings
* **League Integration:**
  * When modifying match flow, ensure compatibility with both free play (no player data) and official matches (has player IDs and match ID)
  * Official matches triggered by `start_competition` event (from league menu selection)
  * Free play uses generic `set_game_mode` without player context
