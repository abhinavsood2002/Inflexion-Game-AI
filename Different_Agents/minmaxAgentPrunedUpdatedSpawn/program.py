# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from library.heuristics import *
import numpy as np
import random
from copy import deepcopy
import math
from collections import defaultdict
DIRECTIONS = (HexDir.DownRight, HexDir.Down, HexDir.DownLeft, HexDir.UpLeft, HexDir.Up, HexDir.UpRight)
CUTOFF_DEPTH = 3
START_GAME = 15

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
        self._ref = dict()
        match color:
            case PlayerColor.RED:
                print("UpdatedSpawn I am playing as red")
            case PlayerColor.BLUE:
                print("UpdatedSpawn: I am playing as blue")

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        global CUTOFF_DEPTH
        global START_GAME

        self._ref = referee
        if self._ref["time_remaining"] != None and self._ref["time_remaining"] < 30:
                CUTOFF_DEPTH = 2
                START_GAME = 0

        if self._turn < START_GAME:
            return self.minimax(self._board, CUTOFF_DEPTH + 1, True, -math.inf, math.inf)[1]
        else:
            return self.minimax(self._board, CUTOFF_DEPTH, True, -math.inf, math.inf)[1]

    def game_over(self, board, turn):
        blue_tokens = {(b_x, b_y): (b_c, b_v) for (b_x, b_y), (b_c, b_v) in board.items() if b_c == PlayerColor.BLUE}
        red_tokens = {(r_x, r_y): (r_c, r_v) for (r_x, r_y), (r_c, r_v) in board.items() if r_c == PlayerColor.RED}
        if (len(blue_tokens) == 0 or len(red_tokens) == 0) and turn > 2:
            return True
        return False
    
    # Our minimax implementation is based on https://papers-100-lines.medium.com/the-minimax-algorithm-and-alpha-beta-pruning-tutorial-in-30-lines-of-python-code-e4a3d97fa144
    def minimax(self, node, depth, isMaximizingPlayer, alpha, beta):
        try:
            
            if depth == 0 or self.game_over(node, self._turn):
                return power_difference_heuristic(node, self._color), None
            
            if isMaximizingPlayer:
                value = -math.inf
                old_difference = token_difference_heuristic(node, self._color)
                for move in self.get_possible_moves(node, self._color):
                    new_node = self.apply_action(node, move, self._color)
                    difference = token_difference_heuristic(new_node, self._color)
                    if difference - old_difference <= 0:
                        continue
                    
                    tmp = self.minimax(new_node, depth-1, False, alpha, beta)[0]
                    if tmp > value:
                        value = tmp
                        best_movement = move
                    
                    if value >= beta:
                        break
                    alpha = max(alpha, value)
            else:
                value = math.inf
                old_difference = token_difference_heuristic(node, self._color)
                for move in self.get_possible_moves(node, self._color.opponent):
                    new_node = self.apply_action(node, move, self._color.opponent)
                    difference = token_difference_heuristic(new_node, self._color)

                    if difference - old_difference >= 0:
                        continue
                    tmp = self.minimax(new_node, depth-1, True, alpha, beta)[0]
                    if tmp < value:
                        value = tmp
                        best_movement = move
                    
                    if value <= alpha:
                        break
                    beta = min(beta, value)
            return value, best_movement
        
        # In rare pruning cases where no moves cause difference in heuristic
        except UnboundLocalError:
            move_values = []
            print("UnboundErrorEncountered")
            for move in self.get_possible_moves(self._board, self._color):
                new_board = self.apply_action(self._board, move, self._color)
                move_values.append((power_difference_heuristic(new_board, self._color), move))
            random.shuffle(move_values)
            return max(move_values, key = lambda x: x[0])
            
    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        self._turn += 1
        self._ref = referee
        match action:
            case SpawnAction(cell):
                if color == PlayerColor.RED:
                    self._board[(cell.r, cell.q)] = (PlayerColor.RED, 1) 
                else:
                    self._board[(cell.r, cell.q)] = (PlayerColor.BLUE, 1)
            case SpreadAction(cell, direction):
                self.spread(self._board, (cell.r, cell.q, direction.r, direction.q), color)
                
    def get_possible_moves(self, board, player_color):
        global START_GAME
        possible_moves = []
        spawns = []
        scary_moves = defaultdict(lambda: 0)
        safe_moves = defaultdict(lambda: 0)
        for i in range(7):
            for j in range(7):
                if not((i, j) in board):
                    if  sum([x[1] for x in board.values()]) < 49:
                        spawns.append(SpawnAction(HexPos(i, j)))

                else:
                    color = board[(i, j)][0]
                    # Opponent can still play anything
                    if color == self._color.opponent:
                        scary_moves[SpawnAction(HexPos((i + 1) % 7, j))] += 1
                        scary_moves[SpawnAction(HexPos(i, (j + 1) % 7))] += 1
                        scary_moves[SpawnAction(HexPos((i - 1) % 7, j))] += 1
                        scary_moves[SpawnAction(HexPos(i, (j - 1) % 7))] += 1
                        scary_moves[SpawnAction(HexPos((i - 1) % 7, (j + 1) % 7))] += 1
                        scary_moves[SpawnAction(HexPos((i + 1) % 7,  (j - 1) % 7))] += 1
                    else:
                        safe_moves[SpawnAction(HexPos((i + 1) % 7, j))] += 1
                        safe_moves[SpawnAction(HexPos(i, (j + 1) % 7))] += 1
                        safe_moves[SpawnAction(HexPos((i - 1) % 7, j))] += 1
                        safe_moves[SpawnAction(HexPos(i, (j - 1) % 7))] += 1
                        safe_moves[SpawnAction(HexPos((i - 1) % 7, (j + 1) % 7))] += 1
                        safe_moves[SpawnAction(HexPos((i + 1) % 7,  (j - 1) % 7))] += 1
                    if color == PlayerColor.BLUE and player_color == PlayerColor.BLUE:
                        for direction in DIRECTIONS:
                            possible_moves.append(SpreadAction(HexPos(i, j), direction))
                    elif color == PlayerColor.RED and player_color == PlayerColor.RED:
                        for direction in DIRECTIONS:
                            possible_moves.append(SpreadAction(HexPos(i,j), direction))  
        random.shuffle(possible_moves)
        random.shuffle(spawns)
        spawns_start = []
        spawns_next = []
        if self._turn < START_GAME and self._color == player_color:
            for move in spawns:
                if (move in scary_moves) and (move in safe_moves):
                    # Remove only for myself
                        if scary_moves[move] < safe_moves[move] - 1:
                            spawns.remove(move)
                            spawns_next.append((move, safe_moves[move] - scary_moves[move]))
                elif move in scary_moves:
                    spawns.remove(move)
                    spawns.append(move)
               
                elif move in safe_moves:
                    spawns.remove(move)
                    spawns_start.append((move, safe_moves[move]))
               
            # Descending sorts
            spawns_start.sort(key=lambda x: -x[1])
            spawns_next.sort(key=lambda x: -x[1])
            spawns = spawns_start + spawns_next + spawns
            possible_moves.extend(spawns)
        else:
            possible_moves.extend(spawns)
            random.shuffle(possible_moves)
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


        
