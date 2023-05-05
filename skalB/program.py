"""
COMP30024 Artificial Intelligence, Semester 1 2023
Project Part B: Game Playing Agent
"""

from agent.logger import Logger
from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir

from agent.board import Board

# This is the entry point for your game playing agent. Currently the agent
# simply spawns a token at the centre of the board if playing as RED, and
# spreads a token at the centre of the board if playing as BLUE. This is
# intended to serve as an example of how to use the referee API -- obviously
# this is not a valid strategy for actually playing the game!

class Agent:
    """
    The agent implemented by us (the students), making the smartest set of
    moves any cohort could have thought of
    """
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """
        self._color = color
        self._current_board = Board()
        self._game_logger = Logger()
        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as red")
            case PlayerColor.BLUE:
                print("Testing: I am playing as blue")

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """

        final_action: Action
        match self._color:
            case PlayerColor.RED:
                final_action = SpawnAction(HexPos(3, 3))
            case PlayerColor.BLUE:
                # This is going to be invalid... BLUE never spawned!
                final_action = SpreadAction(HexPos(3, 3), HexDir.Up)
                final_action = SpawnAction(HexPos(3, 4))

        # self._current_board.append(final_action)
        print(
                f"\nfor color {self._color} | function: action"
                f"\nself._current_board = {self._current_board}\n"
        )
        return final_action

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        result = self._current_board.update_board(action, color)
        self._game_logger.log_board_result(result)
        print(
                f"\nfor color {self._color} | function: turn"
                f"\nself._current_board = {self._current_board}\n"
        )
        match action:
            case SpawnAction(cell):
                print(f"Testing: {color} SPAWN at {cell}")
                pass
            case SpreadAction(cell, direction):
                print(f"Testing: {color} SPREAD from {cell}, {direction}")
                pass
