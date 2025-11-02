import foos.config as config
import os
import time

from foos.process import call_and_log
from foos.platform import is_pi

class Plugin:
    def __init__(self, bus):
        self.bus = bus
        bus.subscribe_map({'replay_request': lambda d: self.replay('long', 'manual', {}),
                           'score_goal': lambda d: self.replay('short', 'goal', d)},
                          thread=True)

    def replay(self, replay_type, trigger, extra={}):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Replay triggered: type=%s, trigger=%s", replay_type, trigger)
        
        extra['type'] = trigger

        call_and_log(["video/generate-replay.sh", config.replay_path,
              str(config.ignore_recent_chunks),
              str(config.long_chunks), str(config.short_chunks)])
        
        logger.info("Replay generated, notifying replay_start")
        self.bus.notify('replay_start', extra)
        
        # Try mp4 first (better compatibility), fallback to h264
        replay_mp4 = os.path.join(config.replay_path, "replay_{}.mp4".format(replay_type))
        replay_h264 = os.path.join(config.replay_path, "replay_{}.h264".format(replay_type))
        replay_file = replay_mp4 if os.path.exists(replay_mp4) else replay_h264
        
        if os.path.exists(replay_file):
            logger.info("Playing replay file: %s", replay_file)
            call_and_log(["video/replay.sh", replay_file, str(config.replay_fps)])
            logger.info("Replay playback finished")
        else:
            logger.warning("Replay file not found: %s", replay_file)
            time.sleep(3)
            
        self.bus.notify('replay_end')
