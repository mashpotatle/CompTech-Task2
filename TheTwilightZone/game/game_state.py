"""
Defines the possible states of The Twilight Zone.

The game state determines which systems should be updated and which
screen should be displayed.
"""

from enum import Enum, auto


class GameState(Enum):
    """Represents the current state of the game."""

    MAIN_MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    DEAD = auto()
    QUIT = auto()