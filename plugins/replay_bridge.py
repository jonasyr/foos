"""
Replay Bridge Plugin - Connects button events to replay generation/playback.

Listens for 'replay_request' bus events (from OK button) and triggers
the camera replay generation and playback scripts.
"""

import subprocess
import logging
import os
import foos.config as config

logger = logging.getLogger(__name__)

class Plugin:
    """Bridge between GPIO button events and replay video system."""
    
    def __init__(self, bus):
        self.bus = bus
        self.bus.subscribe(self.process_event, thread=False)
        logger.info("Replay bridge initialized")
    
    def process_event(self, event):
        """Handle bus events - specifically looking for replay_request."""
        # event is an Event object with .name and .data attributes
        if event.name == 'replay_request':
            kind = event.data.get('kind', 'long') if event.data else 'long'
            # Only handle long press replays (short press is for menu)
            if kind == 'long':
                self.on_replay(kind)
    
    def on_replay(self, kind='short'):
        """
        Generate and play instant replay.
        
        Args:
            kind: 'short' or 'long' - determines which replay duration to use
        """
        try:
            logger.info("Replay requested: %s", kind)
            
            # Get configuration
            base = getattr(config, 'replay_path', '/dev/shm/replay')
            long_chunks = getattr(config, 'long_chunks', 6)
            short_chunks = getattr(config, 'short_chunks', 2)
            fps = getattr(config, 'replay_fps', 25)
            
            # Get absolute path to repo root
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Generate replay files (skip most recent fragment with IGN=1)
            generate_cmd = f'./video/generate-replay.sh {base} 1 {long_chunks} {short_chunks}'
            logger.debug("Running: %s", generate_cmd)
            
            result = subprocess.run(
                ['bash', '-lc', generate_cmd],
                cwd=script_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.error("Replay generation failed: %s", result.stderr)
                return
            
            # Pick replay file based on kind
            replay_file = f'{base}/replay_long.mp4' if kind == 'long' else f'{base}/replay_short.mp4'
            
            if not os.path.exists(replay_file):
                logger.warning("Replay file not found: %s", replay_file)
                return
            
            logger.info("Playing %s replay: %s", kind, replay_file)
            
            # Play replay (non-blocking, don't check exit code as player may return non-zero)
            play_cmd = f'./video/replay.sh {replay_file} {fps}'
            subprocess.run(
                ['bash', '-lc', play_cmd],
                cwd=script_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30
            )
            
            logger.info("Replay playback completed")
            
        except subprocess.TimeoutExpired:
            logger.error("Replay generation/playback timed out")
        except Exception as e:
            logger.error("Replay failed: %s", e, exc_info=True)
