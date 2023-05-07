"""
This is the main class for maintaining our Board based on the player's
previous moves
"""
from typing import Final, Tuple

import numpy as np
from skalB.typedefs import BoardDict, BoardModError, Result, SpreadType, SuccessMessage
from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexDir
from referee.game.hex import HexVec

INITIAL_POINTS: Final[int] = 1

class Board:
    """
    Maintains the board from the point of view of the Agent
    """
    def __init__(self) -> None:
        self.board_dict: BoardDict = dict()

    def update_board(self, action: Action, color: PlayerColor) \
            -> Result[SuccessMessage, BoardModError]:
        """
        Chooses what to do to the board with the given action,
        converting any types as necessary
        """
        direction: HexDir
        result: BoardModError | None
        match action:
            case SpawnAction(cell):
                result = self.spawn(action, color)
            case SpreadAction(cell, direction):
                dir_value: HexVec = direction.value
                fin_tuple = (cell.r, cell.q, dir_value.r, dir_value.q)
                result = self.spread(fin_tuple, color)

        if result is None:
            return SuccessMessage(action, color)
        return result

    def spawn(self, location: SpawnAction, color: PlayerColor) -> Result[None, BoardModError]:
        coordinates = location.cell.r, location.cell.q

        if coordinates in self.board_dict:
            return BoardModError.OCCUPIED_CELL_SPAWN

        color_char: str
        match color:
            case PlayerColor.RED:
                color_char = 'r'
            case PlayerColor.BLUE:
                color_char = 'b'
        self.board_dict[coordinates] = (color_char, INITIAL_POINTS)

    def spread(self, move: SpreadType, player_color: PlayerColor) -> Result[None, BoardModError]:
        """ 
          Based on the given SpreadType tuple, this mutates the input_value board to perform
          a "SpreadType" action, as defined on the Infexion specification
        """
        curr_position = move[0:2]
        if curr_position not in self.board_dict:
            return BoardModError.EMPTY_SPREAD

        found_color = PlayerColor.RED \
            if self.board_dict[curr_position][0] == 'r' \
            else PlayerColor.BLUE

        if found_color != player_color:
            return BoardModError.INVALID_TOKEN_INTERACTION

        direction = move[2:4]
        tokens_to_spread = self.board_dict[curr_position][1]
        for i in range(1, tokens_to_spread + 1):
            # Using numpy as a quick "Hack" for vectorization. Can change if needed.
            new_pos: Tuple[int, int]
            new_pos = tuple((np.array(curr_position) + i * np.array(direction)) % 7)
            assert len(new_pos) == 2
            if new_pos in self.board_dict:
                tokens_at_new_pos = self.board_dict[new_pos][1]

                # Stacks of 6 get deleted on addition of a token.
                if tokens_at_new_pos == 6:
                    del self.board_dict[new_pos]
                else:
                    self.board_dict[new_pos] = (
                        self.board_dict[curr_position][0],
                        tokens_at_new_pos + 1
                    )
            else:
                self.board_dict[new_pos] = (self.board_dict[curr_position][0], 1)
        del self.board_dict[curr_position]
