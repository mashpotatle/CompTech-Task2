"""
Entry point for The Twilight Zone.

This module starts the game application. The main game logic is handled
by the Game class in game/game.py.
"""

from game.game import Game


def main():
    """Create and run the game.""" 

    game = Game()
    game.run()


if __name__ == "__main__":
    main()