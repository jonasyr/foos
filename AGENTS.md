# AGENTS.md: AI Collaboration Guide

This document provides essential context for AI models interacting with this project. Adhering to these guidelines will ensure consistency and maintain code quality.

## 1. Project Overview & Purpose

* **Primary Goal:** Provide an event-driven foosball scorekeeping and instant replay system that runs on a Raspberry Pi, capturing goals, managing replays, integrating with chat services, and optionally syncing with a league service. The UI is rendered with Pi3D and is optimized for kiosk-style deployment with hardware buttons and sensors.
* **Business Domain:** Embedded multimedia application for recreational foosball tables, combining hardware control, live graphics, and media automation.

## 2. Core Technologies & Stack

* **Languages:** Python 3 (primary application logic), C (Raspberry Pi OpenMAX replay player), Bash (setup & maintenance scripts), Arduino sketches for peripheral hardware. No Nim sources are present; treat the codebase as a Python-centric project unless a future migration introduces Nim.
* **Frameworks & Runtimes:** Pi3D for 3D-rendered UI, Python threading/multiprocessing primitives, Raspberry Pi OpenMAX IL stack for video playback (via `bcm_host`/`ilclient`).
* **Databases:** Uses local JSON/flat files (e.g., `league.json`) for league integration; no dedicated database service is configured.
* **Key Libraries/Dependencies:** Pi3D, NumPy, Pillow, google-api-python-client, requests, evdev, inotify_simple, pyserial, RPi.GPIO (or compatible rpi-lgpio), Slack/HipChat clients. Shell utilities include ffmpeg/avconv, sox, and dispmanx tooling.
* **Platforms:** Designed primarily for Raspberry Pi OS (Pi 2/3) with support for direct deployment on X11 desktops for debugging. Video subsystem assumes Raspberry Pi GPU capabilities.
* **Package Manager:** Python dependencies managed through `pip` with `requirements.txt`; C component builds via `make` in `video/player`.

## 3. Architectural Patterns

* **Overall Architecture:** Monolithic event-driven application with a plugin architecture. A central message bus (`foos.bus.Bus`) fans events to plugins that encapsulate individual features (scorekeeping, camera, uploads, league sync, hardware IO).
* **Directory Structure Philosophy:**
  * `/foos`: Core Python package containing bootstrap code (`foos.py`), configuration loaders, platform detection, process helpers, and the Pi3D UI implementation under `foos/ui`.
  * `/plugins`: Feature modules; each file exposes a `Plugin` class that subscribes to bus events and may spawn worker threads for IO.
  * `/video`: Replay tooling, including shell scripts and a C OpenMAX player compiled with the provided `Makefile`.
  * `/arduino`: Firmware sketches and documentation for Arduino-based goal detection hardware.
  * `/doc`: User-facing documentation covering installation, hardware setup, UI, and troubleshooting.
  * `/debug`: Shell helpers to simulate bus events (goal, replay, menu) without hardware.
  * `/tools`: Developer utilities, e.g., movement detection experiments.
  * `/img`, `/sounds`: Static assets consumed by the UI.
  * `/check`, `/boot.sh`, `/main.sh`, `/foos.sh`, `setup-trixie.sh`: Operational scripts for environment verification, bootstrapping, and daemon-style execution.
* **Module Organization:** Core modules live under the `foos` package with single-responsibility files (e.g., `bus.py`, `plugin_handler.py`, `clock.py`). UI code is grouped under `foos/ui`. Plugins are flat modules in `/plugins`; enabling features is driven by `config_base.plugins` overrides loaded through `foos.config`.

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

## 7. Specific Instructions for AI Collaboration

* **Contribution Guidelines:**
  * Follow the plugin-based architecture—prefer adding new capabilities as plugins or extensions of existing ones rather than hard-coding into the core GUI.
  * Maintain thread safety when subscribing to the bus; use the provided `thread=True` flag for long-running handlers and respect queue backpressure.
  * Extend configuration via overrides in `config.py`; do not modify `config_base.py` defaults unless changing project-wide behavior.
  * When altering UI assets, keep resources under `/img` and reference them via `foos/ui/ui.py` helpers (`load_texture`, `img`).
* **Security:** Never hardcode production secrets. Use sample files for tokens (`client_secrets.json.sample`, `config.py.sample`) and document any required environment variables. Be mindful of subprocess calls (`foos/process.py`) and validate/escape inputs when integrating new commands.
* **Dependencies:** Add Python packages to `requirements.txt` and note Raspberry Pi system packages in documentation or `setup-trixie.sh`. For C or shell dependencies, update `video/player/Makefile` or the relevant scripts. Run `pip3 install -r requirements.txt` locally to confirm compatibility.
* **Commit Messages:** Existing history favors descriptive, sentence-style messages summarizing refactors. Keep messages clear about the scope (e.g., “Refactor button handling…”). Conventional Commit prefixes are not currently enforced, but concise summaries are appreciated.

