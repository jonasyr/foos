"""Miscellaneous helpers shared across plugins and UI components."""

import config


def teamName(team):
    """Return the configured display name for a team.

    Args:
        team: Key representing either the ``"yellow"`` or ``"black"`` team.

    Returns:
        Human-friendly team name defined in configuration.
    """

    return config.team_names[team]
