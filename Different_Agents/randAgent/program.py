# COMP30024 Artificial Intelligence, Semester 1 2023
# Project Part B: Game Playing Agent

from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
import numpy as np
import random
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
        return random.choice(self.get_possible_moves())


    def turn(self, color: PlayerColor, action: Action, **referee: dict):
        """
        Update the agent with the last player's action.
        """
        match action:
            case SpawnAction(cell):
                if color == PlayerColor.RED:
                    self._board[(cell.r, cell.q)] = (PlayerColor.RED, 1) 
                else:
                    self._board[(cell.r, cell.q)] = (PlayerColor.BLUE, 1)
            case SpreadAction(cell, direction):
                self._spread((cell.r, cell.q, direction.r, direction.q), color)
                
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
    
    def _spread(self, move, color):
        """ 
        Based on the given SpreadType tuple, this mutates the input board to perform
        a "SpreadType" action, as defined on the Infexion specification
        """
        curr_position = move[0:2]
        direction = move[2:4]
        tokens_to_spread = self._board[curr_position][1]

        for i in range(1, tokens_to_spread + 1):
            # Using numpy as a quick "Hack" for vectorization. Can change if needed.
            new_pos = tuple((np.array(curr_position) + i * np.array(direction)) % 7)
            if new_pos in self._board:
                val = self._board[new_pos][1]
                # Stacks of 6 get deleted on addition of a token.
                if val == 6:
                        del self._board[new_pos]     
                else:
                        self._board[new_pos] = (color, val + 1)
            else:
                self._board[new_pos] = (color, 1)
        del self._board[curr_position]
        
