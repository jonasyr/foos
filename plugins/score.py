#!/usr/bin/python3
"""Score tracking plugin."""

from collections import namedtuple
import logging
import foos.config as config

from foos.clock import Clock

State = namedtuple('State', ['yellow_goals', 'black_goals', 'last_goal'])
logger = logging.getLogger(__name__)


class Plugin:
    """Manage goal events and maintain the current score."""

    def __init__(self, bus):
        """Register event handlers and initialize score state."""

        self.last_goal_clock = Clock('last_goal_clock')
        self.scores = {'black': 0, 'yellow': 0}
        self.bus = bus
        fmap = {'goal_event': self.score,
                'increment_score': lambda d: self.increment(d['team']),
                'decrement_score': lambda d: self.decrement(d['team']),
                'reset_score': lambda d: self.reset()}
        self.bus.subscribe_map(fmap, thread=True)

    def score(self, event):
        """Handle incoming goal events and update the scoreboard."""

        team = event['team']
        if 'duration' in event:
            # check goal duration for minimum
            duration = event['duration']
            if duration < config.min_goal_usecs:
                logger.info("Ignoring short goal - duration %d", duration)
                return

        d = self.last_goal_clock.get_diff()
        if d and d <= config.min_secs_between_goals:
            logger.info("Ignoring goal command %s happening too soon", team)
            return

        self.last_goal_clock.reset()
        self.increment(team)
        data = self.__get_event_data()
        data['team'] = team
        self.bus.notify('score_goal', data)

    def increment(self, team):
        """Increase the score for ``team`` and broadcast the change."""

        s = self.scores.get(team, 0)
        self.scores[team] = (s + 1) % 11
        self.pushState()

    def decrement(self, team):
        """Decrease the score for ``team`` without going below zero."""

        s = self.scores.get(team, 0)
        self.scores[team] = max(s - 1, 0)
        self.pushState()

    def load(self, state):
        """Restore state saved by :meth:`save`."""

        self.scores['yellow'] = state.yellow_goals
        self.scores['black'] = state.black_goals
        self.last_goal_clock.set(state.last_goal)
        self.pushState()

    def save(self):
        """Serialize the current score and last goal timestamp."""

        return State(self.scores['yellow'], self.scores['black'], self.last_goal())

    def reset(self):
        """Reset scores to zero and notify listeners."""

        self.scores = {'black': 0, 'yellow': 0}
        self.last_goal_clock.reset()
        self.bus.notify('score_reset', self.__get_event_data())
        self.pushState()

    def last_goal(self):
        """Return the timestamp of the most recent accepted goal."""

        return self.last_goal_clock.get()

    def __get_event_data(self):
        """Bundle the current score payload for bus notifications."""

        return {'yellow': self.scores['yellow'],
                'black': self.scores['black'],
                'last_goal': self.last_goal()}

    def pushState(self):
        """Publish a ``score_changed`` event with the latest values."""

        self.bus.notify("score_changed", self.__get_event_data())
