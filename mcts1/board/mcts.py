import re
from typing import Final, Dict
from math import sqrt, log10

# Exploration factor
C_FACTOR: Final[int] = 1

class BoardCSV:
    """
    Enforces a new BoardCSV-typed declaration raises an error if not made
    properly
    """
    pattern = re.compile(r"([0-6],[0-6],[rb],\d\n)+")
    def __init__(self, string: str) -> None:
        if not BoardCSV.pattern.match(string):
            raise ValueError("Not a valid CSV representation of the Board")
        self.string = string

    def __str__(self) -> str:
        return self.string

    def __eq__(self, str_value) -> bool:
        return self.string == str_value

class MCTS_Values:
    """
    Representation of the values of a single node in a Monte-Carlo Tree
    """
    def __init__(self, curr_board: BoardCSV) -> None:
        self.num_wins: int = 0
        self.playouts: int = 0
        self.curr_board: BoardCSV = curr_board

    def get_upper_confidence_bound(self, playouts_parent) -> float:
        """
        A selection policy, derived from reinforcement learning to determine
        the priority of a node
        """
        exploitation_term = self.num_wins / self.playouts
        exploration_term = sqrt(log10(playouts_parent) / self.playouts)
        return exploitation_term + C_FACTOR * exploration_term

MCTS = Dict[BoardCSV, MCTS_Values]
