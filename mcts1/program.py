"""
COMP30024 Artificial Intelligence, Semester 1 2023
Project Part B: Game Playing Agent
"""

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir

from mcts1.logger import Logger
from mcts1.board import Board

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
        self.num_moves = 0

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        if referee["time_remaining"] is not None:
            remaining_time: int | float = referee["time_remaining"] # type: ignore
            time_elapsed: int | float = 0
            while (remaining_time - time_elapsed) > 0:
                time_elapsed += self._current_board.train_MCTS(self._color, self.num_moves)
            return self._current_board.find_action()

        for _ in range(100):
            self._current_board.train_MCTS(self._color, self.num_moves)

        return self._current_board.find_action()

    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        result = self._current_board.update_board(action, color)
        self._game_logger.log_board_result(result)
        self.num_moves += 1
        print(f"\n\nnum_moves: {self.num_moves}")
