# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from library.heuristics import *
import numpy as np
import random
from copy import deepcopy
import math

DIRECTIONS = (HexDir.DownRight, HexDir.Down, HexDir.DownLeft, HexDir.UpLeft, HexDir.Up, HexDir.UpRight)
CUTOFF_DEPTH = 3
# This is the entry point for your game playing agent. Currently the agent
# simply spawns a token at the centre of the board if playing as RED, and
# spreads a token at the centre of the board if playing as BLUE. This is
# intended to serve as an example of how to use the referee API -- obviously
# this is not a valid strategy for actually playing the game!

class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        Initialise the agent.
        """
        self._color = color
        self._board = dict()
        self._turn = 0
        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as red")
            case PlayerColor.BLUE:
                print("Testing: I am playing as blue")
    
    def game_just_started(self):
        if self._turn < 10:
            return 1
        else:
            return 0

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        print(power_difference_heuristic(self._board, self._color))
        if power_difference_heuristic(self._board, self._color) > 15:
            move_values = []
            for move in self.get_possible_moves(self._board, self._color):
                new_board = self.apply_action(self._board, move, self._color)
                move_values.append((move, power_difference_heuristic(new_board, self._color)))
            random.shuffle(move_values)
            return max(move_values, key = lambda x: x[1])[0]
        
        return self.minimax(self._board, CUTOFF_DEPTH, True, -math.inf, math.inf)[1]

    def game_over(self, board, turn):
        blue_tokens = {(b_x, b_y): (b_c, b_v) for (b_x, b_y), (b_c, b_v) in board.items() if b_c == PlayerColor.BLUE}
        red_tokens = {(r_x, r_y): (r_c, r_v) for (r_x, r_y), (r_c, r_v) in board.items() if r_c == PlayerColor.RED}
        if (len(blue_tokens) == 0 or len(red_tokens) == 0) and turn > 2:
            return True
        return False
    
    # Our minimax implementation is based on https://papers-100-lines.medium.com/the-minimax-algorithm-and-alpha-beta-pruning-tutorial-in-30-lines-of-python-code-e4a3d97fa144
    def minimax(self, node, depth, isMaximizingPlayer, alpha, beta):
        if depth == 0 or self.game_over(node, self._turn):
            return power_difference_heuristic(node, self._color), None

        if isMaximizingPlayer:
            value = -math.inf
            for move in self.get_possible_moves(node, self._color):
                new_node = self.apply_action(node, move, self._color)
                tmp = self.minimax(new_node, depth-1, False, alpha, beta)[0]
                if tmp > value:
                    value = tmp
                    best_movement = move
                
                if value >= beta:
                    break
                alpha = max(alpha, value)
        else:
            value = math.inf
            for move in self.get_possible_moves(node, self._color.opponent):
                new_node = self.apply_action(node, move, self._color.opponent)
                tmp = self.minimax(new_node, depth-1, True, alpha, beta)[0]
                if tmp < value:
                    value = tmp
                    best_movement = move
                
                if value <= alpha:
                    break
                beta = min(beta, value)
        return value, best_movement
        
    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        self._turn += 1
        match action:
            case SpawnAction(cell):
                if color == PlayerColor.RED:
                    self._board[(cell.r, cell.q)] = (PlayerColor.RED, 1) 
                else:
                    self._board[(cell.r, cell.q)] = (PlayerColor.BLUE, 1)
            case SpreadAction(cell, direction):
                self.spread(self._board, (cell.r, cell.q, direction.r, direction.q), color)
                
    def get_possible_moves(self, board, player_color):
        spawns = []
        spreads = {6: [], 5: [], 4: [], 3: [], 2: [], 1: []}
        total_power = sum([x[1] for x in board.values()])
        for i in range(7):
            for j in range(7):
                if not((i, j) in board):
                    if total_power < 49:
                        spawns.append(SpawnAction(HexPos(i, j)))
                else:
                    color, tokens_at = board[(i, j)]
                    if color == PlayerColor.BLUE and player_color == PlayerColor.BLUE:
                        for direction in DIRECTIONS:
                            spreads[tokens_at].append(SpreadAction(HexPos(i, j), direction))
                    elif color == PlayerColor.RED and player_color == PlayerColor.RED:
                        for direction in DIRECTIONS:
                            spreads[tokens_at].append(SpreadAction(HexPos(i, j), direction))
        importance_of_spawns = 0
        random.shuffle(spawns)
        if self.game_just_started:
            possible_moves = spawns + spreads[6] + spreads[5] + spreads[4] + spreads[3] + spreads[2] + spreads[1]
        else:
            possible_moves = spreads[6] + spreads[5] + spreads[4] + spreads[3] + spreads[2] + spreads[1] + spawns 
        return possible_moves
    
    def spread(self, board, move, color):
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

    def apply_action(self, board, action, color):
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
                self.spread(new_board, (cell.r, cell.q, direction.r, direction.q), color)
        return new_board


        
