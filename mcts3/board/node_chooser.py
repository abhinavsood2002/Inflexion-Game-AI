"""
The place to implement heuristic-like functions
"""
from typing import Generator, List
from copy import deepcopy
import math
import numpy as np
from mcts3.typedefs import BoardDict, ColorChar
from mcts3.library.heuristics import token_difference_heuristic, power_difference_heuristic
from referee.game.actions import Action, SpawnAction, SpreadAction
from referee.game.hex import HexDir, HexPos
from referee.game.player import PlayerColor

ALL_HEX_DIRS = [e.value for e in HexDir]
DIRECTIONS = list(HexDir)
PC_MAP = {'r': PlayerColor.RED, 'b': PlayerColor.BLUE}
CUTOFF_DEPTH = 2

def greedy_action(board, color_char: ColorChar, turn_num: int) -> Generator[Action, None, None]:
    move_values = []
    color: PlayerColor = PC_MAP[color_char]
    board = make_greedy_board(board)

    for i in minimax(board, CUTOFF_DEPTH, True, -math.inf, math.inf, color, turn_num, board):
        yield i[1]

    for move in get_possible_moves(board, color):
        new_board = apply_action(board, move, color)
        move_values.append((move, power_difference_heuristic(new_board, color)))
    # shuffle(move_values)
    move_values.sort(key = lambda x: x[1], reverse=True)
    for i in move_values:
        assert move_values[0] == max(move_values, key=lambda x: x[1])
        yield i[0]

def get_possible_moves(board: BoardDict, curr_color: PlayerColor):
    possible_moves: List[Action] = []
    for i in range(7):
        for j in range(7):
            if not (i, j) in board:
                if sum(x[1] for x in board.values()) < 49:
                    possible_moves.append(SpawnAction(HexPos(i, j)))
            else:
                color = board[(i, j)][0]
                if color == PlayerColor.BLUE and curr_color == PlayerColor.BLUE:
                    for direction in DIRECTIONS:
                        possible_moves.append(SpreadAction(HexPos(i, j), direction))
                elif color == PlayerColor.RED and curr_color == PlayerColor.RED:
                    for direction in DIRECTIONS:
                        possible_moves.append(SpreadAction(HexPos(i,j), direction))
    return possible_moves

def apply_action(board, action, color):
    new_board = deepcopy(board)
    match action:
        case SpawnAction(cell):
            if color == PlayerColor.RED:
                # 0 represents red
                new_board[(cell.r, cell.q)] = (PlayerColor.RED, 1) 
            else:
                # 1 represents blue
                new_board[(cell.r, cell.q)] = (PlayerColor.BLUE, 1)
        case SpreadAction(cell, direction):
            spread(new_board, (cell.r, cell.q, direction.r, direction.q), color)
    return new_board

def spread(board, move, color):
    """ 
    Based on the given SpreadType tuple, this mutates the input board to perform
    a "SpreadType" action, as defined on the Infexion specification
    """
    curr_position = move[0:2]
    direction = move[2:4]
    tokens_to_spread = board[curr_position][1]

    for i in range(1, tokens_to_spread + 1):
        # Using numpy as a quick "Hack" for vectorization. Can change if needed.
        new_pos = tuple((np.array(curr_position) + i * np.array(direction)) % 7)
        if new_pos in board:
            val = board[new_pos][1]
            # Stacks of 6 get deleted on addition of a token.
            if val == 6:
                del board[new_pos]
            else:
                board[new_pos] = (color, val + 1)
        else:
            board[new_pos] = (color, 1)
    del board[curr_position]

def make_greedy_board(board: BoardDict):
    fin_board = dict()
    mapper = {'r': PlayerColor.RED, 'b': PlayerColor.BLUE}
    for (coordinates, (color, power)) in board.items():
        fin_board[coordinates] = (mapper[color], power)
    return fin_board

# Our minimax implementation is based on https://papers-100-lines.medium.com/the-minimax-algorithm-and-alpha-beta-pruning-tutorial-in-30-lines-of-python-code-e4a3d97fa144
def minimax(node, depth, isMaximizingPlayer, alpha, beta, color, turn, board):
    try:
        if depth == 0 or game_over(node, turn):
            yield power_difference_heuristic(node, color), None

        if isMaximizingPlayer:
            value = -math.inf
            old_difference = token_difference_heuristic(node, color)
            for move in get_possible_moves(node, color):
                new_node = apply_action(node, move, color)
                difference = token_difference_heuristic(new_node, color)
                if difference - old_difference <= 0:
                    continue

                tmp = minimax(new_node, depth-1, False, alpha, beta, color, turn, board).__next__()[0]
                if tmp > value:
                    value = tmp
                    best_movement = move
                
                if value >= beta:
                    break
                alpha = max(alpha, value)
        else:
            value = math.inf
            old_difference = token_difference_heuristic(node, color)
            for move in get_possible_moves(node, color.opponent):
                new_node = apply_action(node, move, color.opponent)
                difference = token_difference_heuristic(new_node, color)

                if difference - old_difference >= 0:
                    continue
                tmp = minimax(new_node, depth-1, False, alpha, beta, color, turn, board).__next__()[0]
                if tmp < value:
                    value = tmp
                    best_movement = move

                if value <= alpha:
                    break
                beta = min(beta, value)
        yield value, best_movement
    except UnboundLocalError:
        move_values = []
        print("UnboundErrorEncountered")
        for move in get_possible_moves(board, color):
            new_board = apply_action(board, move, color)
            move_values.append((move, power_difference_heuristic(new_board, color)))
        move_values.sort(key= lambda x: x[1], reverse=True)
        for i in move_values:
            yield i[0]

def game_over(board, turn):
    blue_tokens = {(b_x, b_y): (b_c, b_v) for (b_x, b_y), (b_c, b_v) in board.items() if b_c == PlayerColor.BLUE}
    red_tokens = {(r_x, r_y): (r_c, r_v) for (r_x, r_y), (r_c, r_v) in board.items() if r_c == PlayerColor.RED}
    if (len(blue_tokens) == 0 or len(red_tokens) == 0) and turn > 2:
        return True
    return False

