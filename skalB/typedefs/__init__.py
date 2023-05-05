"""
This file serves to outline the different type abstractions used for the
board for making function definitions explicit yet understandable
"""

from typing import Dict, Tuple, Union
from enum import Enum

from referee.game.actions import Action
from referee.game.player import PlayerColor

SpreadType = Tuple[int, int, int, int]
BoardKey = Tuple[int, int]
BoardValue = Tuple[str, int]
BoardDict = Dict[BoardKey, BoardValue]
CellPosition = Tuple[int, int]
Result = Union

class BoardModError(Enum):
    """
    For all errors relating to board modifications
    """
    EMPTY_SPREAD = \
            "Spread cannot be done on a position which is empty"
    INVALID_TOKEN_INTERACTION = \
            "Cannot interact with token which is not your color"
    OCCUPIED_CELL_SPAWN = \
            "Cannot spawn in an occupied cell"

class SuccessMessage:
    """
    Generates a message indicating that a successful action took place
    """
    def __init__(self, action: Action, color: PlayerColor) -> None:
        self.action = action
        self.color = color

    def __str__(self) -> str:
        return f"Successfully executed {self.action} for {self.color}"

