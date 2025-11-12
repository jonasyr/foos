#!/usr/bin/python3
"""
Stats Event Logger Plugin for Foos

This plugin logs goal-by-goal statistics ONLY for official tournament matches
(started via start_competition event). Free play matches are ignored since
player information is not available.

Key Events:
- start_competition: Official match starts (has player data from foos-tournament)
- goal_event: Goal scored by either team
- decrement_score: Score correction (manual adjustment)
- win_game: Match ends with final score
- cancel_competition: Match cancelled

The plugin tracks the timeline of goals and sends them to foos-tournament's
stats API for detailed analytics (ELO, H2H, partnerships, etc.).
"""
import time
import json
import logging
import foos.config as config

try:
    import urllib.request
    import urllib.error
except ImportError:
    urllib = None

logger = logging.getLogger(__name__)


class Plugin:
    def __init__(self, bus):
        self.bus = bus
        self.reset()
        
        # Subscribe to competition events (not menu events!)
        bus.subscribe_map({
            'start_competition': self.on_match_start,
            'win_game': self.on_match_end,
            'cancel_competition': self.on_match_cancel,
            'goal_event': self.on_goal,
            'decrement_score': self.on_decrement
        }, thread=True)
        
        logger.info("Stats event logger initialized")

    def reset(self):
        """Reset state for a new match"""
        self.active = False
        self.t0 = None
        self.score_y = 0
        self.score_b = 0
        self.events = []
        self.match_data = None
        self.tournament_match_id = None

    def on_match_start(self, event):
        """
        Called when an official tournament match starts.
        Only these matches have player information.
        """
        self.reset()
        self.active = True
        self.t0 = time.monotonic()
        
        # Store match data which includes:
        # - 'id': tournament match ID
        # - 'players': list of player names
        # - 'division': division name
        # - 'submatches': game configuration
        self.match_data = event.data if hasattr(event, 'data') else event
        
        # Get the tournament match ID (this is the official match from foos-tournament)
        if isinstance(self.match_data, dict):
            self.tournament_match_id = self.match_data.get('id')
            logger.info("Started tracking official match ID %s with players: %s",
                       self.tournament_match_id,
                       self.match_data.get('players', []))
        else:
            logger.warning("Match start event has no data, cannot track stats")
            self.active = False

    def on_goal(self, event):
        """
        Called when a goal is scored.
        Only logged if we're tracking an active tournament match.
        """
        if not self.active:
            return
            
        # Extract team from event (can be dict or string)
        team = event.data.get('team') if hasattr(event, 'data') else event
        if isinstance(event, dict):
            team = event.get('team')
            
        if team == 'yellow':
            self.score_y += 1
        elif team == 'black':
            self.score_b += 1
        else:
            logger.warning("Unknown team in goal_event: %s", team)
            return
            
        # Calculate elapsed time since match start
        elapsed = int(time.monotonic() - self.t0)
        
        # Record the goal event with timestamp and running score
        goal_event = {
            'team': team,
            't': elapsed,
            'score_yellow': self.score_y,
            'score_black': self.score_b
        }
        self.events.append(goal_event)
        
        logger.debug("Goal logged: %s at t=%ds (Y:%d B:%d)",
                    team, elapsed, self.score_y, self.score_b)

    def on_decrement(self, event):
        """
        Called when score is manually decremented (correction).
        Keeps our local tracking in sync with actual score.
        """
        if not self.active:
            return
            
        team = event.data.get('team') if hasattr(event, 'data') else event
        if isinstance(event, dict):
            team = event.get('team')
            
        if team == 'yellow' and self.score_y > 0:
            self.score_y -= 1
            logger.debug("Yellow score decremented to %d", self.score_y)
        elif team == 'black' and self.score_b > 0:
            self.score_b -= 1
            logger.debug("Black score decremented to %d", self.score_b)

    def on_match_end(self, event):
        """
        Called when match ends (win_game event).
        Upload goal timeline to foos-tournament API.
        """
        if not self.active:
            return
            
        logger.info("Match ended. Uploading %d goal events for match ID %s",
                   len(self.events), self.tournament_match_id)
        
        # Only upload if we have a valid tournament match ID
        if not self.tournament_match_id:
            logger.warning("No tournament match ID, skipping stats upload")
            self.reset()
            return
            
        # Upload goal timeline if we have the extended API endpoints
        if hasattr(config, 'league_stats_api') and config.league_stats_api:
            self._upload_goal_timeline()
        else:
            logger.info("league_stats_api not configured, skipping goal timeline upload")
            
        self.reset()

    def on_match_cancel(self, event):
        """Called when match is cancelled - just reset state"""
        if self.active:
            logger.info("Match cancelled, clearing stats buffer")
        self.reset()

    def _upload_goal_timeline(self):
        """
        Upload goal-by-goal timeline to foos-tournament stats API.
        
        This requires the extended API endpoints described in the build plan
        (Part 4). If those endpoints aren't available, this will fail silently.
        """
        if not urllib:
            logger.warning("urllib not available, cannot upload stats")
            return
            
        if not self.events:
            logger.info("No goal events to upload")
            return
            
        try:
            base_url = config.league_url.rstrip('/')
            api_key = getattr(config, 'league_apikey', None)
            
            if not api_key:
                logger.warning("No league_apikey configured, cannot upload stats")
                return
                
            # Prepare request
            url = f"{base_url}/matches/{self.tournament_match_id}/goals"
            payload = {'events': self.events}
            body = json.dumps(payload).encode('utf-8')
            headers = {
                'X-API-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            # Send request
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                result = response.read().decode('utf-8')
                logger.info("Goal timeline uploaded successfully: %s", result)
                
        except urllib.error.HTTPError as e:
            logger.error("HTTP error uploading goal timeline: %s - %s", e.code, e.reason)
            if e.code == 404:
                logger.error("API endpoint not found - ensure foos-tournament has the stats API routes")
        except urllib.error.URLError as e:
            logger.error("Network error uploading goal timeline: %s", e.reason)
        except Exception as e:
            logger.error("Unexpected error uploading goal timeline: %s", e)
