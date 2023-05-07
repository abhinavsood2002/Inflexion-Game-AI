# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
from library.heuristics import *
import numpy as np
import random
from copy import deepcopy

DIRECTIONS = (HexDir.DownRight, HexDir.Down, HexDir.DownLeft, HexDir.UpLeft, HexDir.Up, HexDir.UpRight)

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

        match color:
            case PlayerColor.RED:
                print("Testing: I am playing as red")
            case PlayerColor.BLUE:
                print("Testing: I am playing as blue")

    def action(self, **referee: dict) -> Action:
        """
        Return the next action to take.
        """
        move_values = []
        
        for move in self.get_possible_moves():
            new_board = self.apply_action(self._board, move, self._color)
            blue_tokens = {(b_x, b_y): (b_c, b_v) for (b_x, b_y), (b_c, b_v) in new_board.items() if b_c == PlayerColor.BLUE}
            red_tokens = {(r_x, r_y): (r_c, r_v) for (r_x, r_y), (r_c, r_v) in new_board.items() if r_c == PlayerColor.RED}
            move_values.append((move, power_difference_heuristic(red_tokens, blue_tokens, self._color)))
        random.shuffle(move_values)
        return max(move_values, key = lambda x: x[1])[0]


    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        match action:
            case SpawnAction(cell):
                if color == PlayerColor.RED:
                    # 0 represents red
                    self._board[(cell.r, cell.q)] = (PlayerColor.RED, 1) 
                else:
                    # 1 represents blue
                    self._board[(cell.r, cell.q)] = (PlayerColor.BLUE, 1)
            case SpreadAction(cell, direction):
                self.spread(self._board, (cell.r, cell.q, direction.r, direction.q), color)
                
    def get_possible_moves(self):
        possible_moves = []
        for i in range(7):
            for j in range(7):
                if not((i, j) in self._board):
                    if  sum([x[1] for x in self._board.values()]) < 49:
                        possible_moves.append(SpawnAction(HexPos(i, j)))
                else:
                    color = self._board[(i, j)][0]
                    if color == PlayerColor.BLUE and self._color == PlayerColor.BLUE:
                        for direction in DIRECTIONS:
                            possible_moves.append(SpreadAction(HexPos(i, j), direction))
                    elif color == PlayerColor.RED and self._color == PlayerColor.RED:
                        for direction in DIRECTIONS:
                            possible_moves.append(SpreadAction(HexPos(i,j), direction))  
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
        
        
