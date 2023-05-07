"""
This is the main class for maintaining our Board based on the player's
previous moves
"""
from agent.typedefs import BoardDict, BoardModError, Result, SpreadType
from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir

import numpy as np

class Board:
    def __init__(self) -> None:
        self.board_dict: BoardDict = dict()

    def spawn(self, location: SpawnAction, color: PlayerColor) -> Result[None, BoardModError]:
        INITIAL_POINTS = 1
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
            new_pos = tuple((np.array(curr_position) + i * np.array(direction)) % 7)
            if new_pos in self.board_dict:
                tokens_at_new_pos = self.board_dict[new_pos][1]
                
                # Stacks of 6 get deleted on addition of a token.
                if tokens_at_new_pos == 6:
                    del self.board_dict[new_pos]
                else:
                    self.board_dict[new_pos] = (self.board_dict[curr_position][0], tokens_at_new_pos + 1)
            else:
                self.board_dict[new_pos] = (self.board_dict[curr_position][0], 1)
        del self.board_dict[curr_position]
