"""
This is the main class for maintaining our Board based on the player's
previous moves
"""
from time import time
from typing import Dict, Union as Result, Final, Tuple, Optional
from copy import deepcopy

import numpy as np
from mcts2.board.mcts import MCTS, BoardCSV, MCTS_Values
from mcts2.board.node_chooser import greedy_action
from mcts2.typedefs import BoardDict, BoardModError, ColorChar, SpreadType, SuccessMessage
from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexDir
from referee.game.hex import HexPos, HexVec

INITIAL_POINTS: Final[int] = 1

class Board:
    """
    Maintains the board from the point of view of the Agent
    """
    # Father of all MCTS nodes
    adam: MCTS = {}
    actions: Dict[str, Action] = {}

    def __init__(self, board_dict: Optional[BoardDict] = None) -> None:
        if board_dict is None:
            board_dict = {}
        self.board_dict: BoardDict = board_dict

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

    def spawn(self, location: SpawnAction, color: PlayerColor) \
        -> Result[None, BoardModError]:
        """
        Spawn a piece at the board
        """
        coordinates = location.cell.r, location.cell.q

        if coordinates in self.board_dict:
            return BoardModError.OCCUPIED_CELL_SPAWN

        color_char: ColorChar
        match color:
            case PlayerColor.RED:
                color_char = 'r'
            case PlayerColor.BLUE:
                color_char = 'b'
        self.board_dict[coordinates] = (color_char, INITIAL_POINTS)
        return None

    def spread(self, move: SpreadType, player_color: PlayerColor) \
        -> Result[None, BoardModError]:
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
            calc_pos = tuple((np.array(curr_position) + i * np.array(direction)) % 7)
            new_pos = (int(calc_pos[0]), int(calc_pos[1]))
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

        return None

    @staticmethod
    def from_BoardCSV(board: BoardCSV) -> 'Board':
        """
        Converts the current board_csv into a Board type
        """
        board_dict = parse_input(str(board))
        return Board(board_dict)

    def train_MCTS(self, color: PlayerColor, num_moves: int) -> float:
        """
        Executes the Monte Carlo Tree Search algorithm to keep building the
        Monte Carlo tree
        Return: The time it took to build the tree
        """
        starting_time = time()

        original_board: BoardCSV = BoardCSV.from_Board(self.board_dict)
        chosen_node: MCTS_Values
        if original_board not in Board.adam:
            chosen_node = MCTS_Values(original_board, color=color)
            Board.adam[original_board] = chosen_node
            # print(f"\n\nOVER HERE\n\nBoard.adam: {Board.adam}")
        else:
            chosen_node = Board.adam[original_board]

        while chosen_node.playouts != 0:
            # Use MCTS_Values to get upper_confidence bounds to choose a child
            children = chosen_node.children.items()

            if len(children) <= 25:
                break

            playouts: int = chosen_node.playouts
            chosen_node = max(
                children,
                key=lambda x: x[1].get_upper_confidence_bound(playouts)
            )[1]

        # Expand the chosen node once
        curr_board: Board = Board.from_BoardCSV(chosen_node.curr_board)

        new_action: Action
        if len(curr_board.board_dict) == 0:
            new_action = SpawnAction(HexPos(3, 3))
            curr_board.update_board(new_action, color)
            new_board: BoardCSV = BoardCSV.from_Board(curr_board.board_dict)
        else:
            color_char: ColorChar = 'r' \
                    if color == PlayerColor.RED \
                    else 'b'
            action_iter = greedy_action(curr_board.board_dict, color_char)
            new_action = action_iter.__next__()
            new_board = self.get_new_board(color, curr_board, new_action)
            while new_board in chosen_node.children:
                new_action = action_iter.__next__()
                new_board = self.get_new_board(color, curr_board, new_action)

        board_connector = original_board.get_BoardCSV_connector(new_board)
        Board.actions[board_connector] = new_action
        new_node = MCTS_Values(new_board, chosen_node)

        # Execute playout
        increment = new_node.do_playout(curr_board, num_moves + 1)

        inverse_increment_map = {
            0 : 1, 1 : 0, 0.5 : 0.5
        }

        for board_csv in new_node.derives_from:
            curr_board_csv = Board.adam[board_csv]
            if curr_board_csv.color_to_move == color:
                curr_board_csv.num_wins += increment
            else:
                curr_board_csv.num_wins += inverse_increment_map[increment]
            curr_board_csv.playouts += 1

        chosen_node.children[new_board] = new_node
        # Add the modified version of the current line
        Board.adam[new_board] = new_node
        # TODO: Find a way to export the data to json for pre-loading data
        # TODO: Implement (in __init__) a way to load the pre-trained data
        return time() - starting_time

    def get_new_board(self, color, curr_board, new_action):
        candidate_board = deepcopy(curr_board)
        candidate_board.update_board(new_action, color)
        new_board = BoardCSV.from_Board(candidate_board.board_dict)
        return new_board

    def find_action(self) -> Action:
        """
        Finds the best action to take based on the created MCTS tree
        """
        original_board: BoardCSV = BoardCSV.from_Board(self.board_dict)
        chosen_node = Board.adam[original_board]
        most_playouts_node = max(
            chosen_node.children.items(),
            key=lambda x: x[1].playouts
        )[0]
        board_connector = original_board.get_BoardCSV_connector(most_playouts_node)
        return Board.actions[board_connector]

def parse_input(board_csv: str) -> BoardDict:
    """
    Parse board_csv into a dictionary of board cell states.
    """
    return { # type: ignore
        (int(r), int(q)): (p.strip(), int(k)) # type: ignore
        for r, q, p, k in [
            line.split(',') for line in board_csv.splitlines()
            if len(line.strip()) > 0
        ]
    }
