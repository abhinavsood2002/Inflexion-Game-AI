"""
File that carries out the responsilities of initiating and performing the
Monte Carlo Tree Search algorithm
"""
from copy import deepcopy
import re
from typing import Final, Dict, List, NewType, Optional, Set
from math import sqrt, log10
from mcts1.board import node_chooser
from mcts1.typedefs import BoardDict, BoardKey, GameState

from referee.game.player import PlayerColor


# Exploration factor
C_FACTOR: Final[int] = 1
ENDGAME: Set[GameState] = {
    GameState.BLUE_WINS,
    GameState.RED_WINS,
    GameState.DRAW
}
MAX_NUM_MOVES: Final[int] = 343
# MAX_NUM_MOVES: Final[int] = 10

class BoardCSV:
    """
    Enforces a new BoardCSV-typed declaration raises an error if not made
    properly
    """
    # valid pattern:   "1,2,r,3\n"
    # invalid pattern: "1,2,r,3"
    # invalid pattern: "1,2,a,3\n"
    # invalid pattern: "1,9,r,3\n"
    # invalid pattern: "1, 2, r, 3\n"
    pattern = re.compile(r"([0-6],[0-6],[rb],\d\n)+")
    def __init__(self, string: str) -> None:
        if len(string) > 0 and not BoardCSV.pattern.match(string):
            raise ValueError(f"Not a valid CSV representation of the Board\n{string}\n")
        self.string = string

    def __str__(self) -> str:
        return self.string

    def __eq__(self, str_value) -> bool:
        return self.string == str_value

    @staticmethod
    def from_Board(board: BoardDict) -> 'BoardCSV':
        """
        Makes a BoardCSV object from a non-empty BoardDict
        """
        tokens: List[BoardKey] = sorted(
            list(board),
            key=lambda x: int(f"{x[0]}{x[1]}"))

        fin_str = ""
        for r_value, q_value in tokens:
            color, points = board[(r_value, q_value)]
            fin_str += f"{r_value},{q_value},{color},{points}\n"
        return BoardCSV(fin_str)

    def __hash__(self) -> int:
        return hash(self.string)

    def get_BoardCSV_connector(self, other: 'BoardCSV') -> str:
        """
        Returns a JSON-storable connector between two board states
        """
        return f"{self.string} | {str(other)}"

class MCTS_Values:
    """
    Representation of the values of a single node in a Monte-Carlo Tree
    """
    def __init__(self, curr_board: BoardCSV, parent: Optional['MCTS_Values'] = None, color: Optional[PlayerColor] = None) -> None:
        # float because of the possibility of a draw
        self.num_wins: int | float = 0
        self.playouts: int = 0
        self.curr_board: BoardCSV = curr_board
        self.derives_from: Set[BoardCSV] = set()
        self.children: MCTS = {}
        self.color_to_move: PlayerColor
        assert(parent is not None or color is not None)
        chosen_color: PlayerColor
        if parent is not None:
            self.derives_from.update(parent.derives_from)
            self.derives_from.add(parent.curr_board)
            chosen_color = PlayerColor.BLUE \
                    if parent.color_to_move == PlayerColor.RED \
                    else PlayerColor.RED
        else:
            assert color is not None
            chosen_color = color
        self.color_to_move = chosen_color

    def get_upper_confidence_bound(self, playouts_parent) -> float:
        """
        A selection policy, derived from reinforcement learning to determine
        the priority of a node
        """
        if self.playouts == 0:
            # Avoid zero-division error
            return 10;
        exploitation_term = self.num_wins / self.playouts
        exploration_term = sqrt(log10(playouts_parent) / self.playouts)
        return exploitation_term + C_FACTOR * exploration_term

    def do_playout(self, board, num_moves: int): # type: ignore
        """
        Executes the playout of the game, only noting down the final result
        """
        board = deepcopy(board) # type: ignore
        curr_game_state = get_game_state(board, num_moves)
        current_player: PlayerColor = PlayerColor.RED \
                if self.color_to_move == PlayerColor.BLUE \
                else PlayerColor.BLUE
        while curr_game_state not in ENDGAME:
            # track(board, "prev board:", "tracker.txt")
            next_action = node_chooser \
                    .generate_action(board, current_player) \
                    .__next__()
            # track(board, "curr board", "tracker1.txt")
            board.update_board(next_action, current_player)
            num_moves += 1
            curr_game_state = get_game_state(board, num_moves)
            current_player = PlayerColor.RED \
                if current_player == PlayerColor.BLUE \
                else PlayerColor.BLUE

        winning_color: PlayerColor = PlayerColor.RED \
                if curr_game_state == GameState.RED_WINS \
                else PlayerColor.BLUE

        increment: int | float
        if winning_color == self.color_to_move:
            increment = 1
        elif curr_game_state == GameState.DRAW:
            increment = 0.5
        else:
            # Assumption: The player must have lost at this point
            increment = 0

        self.num_wins += increment
        self.playouts += 1
        return increment

def get_game_state(board, num_moves) -> GameState: # type: ignore
    """
    Checks what the current state of the game is
    """
    num_reds, num_blues = 0, 0
    for (_, (color, _)) in board.board_dict.items(): # type: ignore
        match color:
            case 'r':
                num_reds += 1
            case 'b':
                num_blues += 1

    if num_moves >= MAX_NUM_MOVES:
        if num_reds > num_blues:
            return GameState.RED_WINS
        if num_blues > num_reds:
            return GameState.BLUE_WINS
        return GameState.DRAW

    if num_blues == 0 or num_reds == 0:
        return GameState.BLUE_WINS if num_reds == 0 else GameState.RED_WINS

    return GameState.PLAYING

def track(board, message: str, filename: str):
    finstring = f"\n\n{message}"
    with open(filename, 'w', encoding='utf-8') as file:
        board_keys = list(board.board_dict)
        board_keys.sort(key=lambda x: int(f"{x[0]}{x[1]}"))
        for i in board_keys:
            finstring += f"{i}:{board.board_dict[i]}\n"
        file.write(finstring)

MCTS = Dict[BoardCSV, MCTS_Values]
