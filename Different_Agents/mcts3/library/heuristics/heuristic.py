from referee.game import \
    PlayerColor, Action, SpawnAction, SpreadAction, HexPos, HexDir
import numpy as np
import math
DIRECTIONS = (HexDir.DownRight, HexDir.Down, HexDir.DownLeft, HexDir.UpLeft, HexDir.Up, HexDir.UpRight)

def surround_heuristic(red_tokens, blue_tokens, player_color):

    # Swap if different color
    if player_color == PlayerColor.BLUE:
        intermediate = red_tokens
        red_tokens = blue_tokens
        blue_tokens = intermediate
    
    surround_value = 0
    for k, v in blue_tokens.items():
        for direction in DIRECTIONS:
            neighbouring_pos = tuple((np.array(k) + np.array((direction.r, direction.q))) % 7)            
            if neighbouring_pos in red_tokens:
                if red_tokens[neighbouring_pos][1] >= 2:
                    surround_value += 2
                else:
                    surround_value += 1
            elif neighbouring_pos in blue_tokens:
                if blue_tokens[neighbouring_pos][1] >= 2:
                    surround_value -= 2
                else:
                    surround_value -= 1

    return surround_value

def token_difference_heuristic(board, player_color):
    red_proportion = 0
    for (c, v) in board.values():
        if c == PlayerColor.RED:
            red_proportion += 1
        else:
            red_proportion -= 1
    if player_color == PlayerColor.RED:
        return red_proportion
    else:
        return -1 * red_proportion

def power_difference_heuristic(board, player_color):
    red_proportion = 0
    for (c, v) in board.values():
        if c == PlayerColor.RED:
            red_proportion += v
        else:
            red_proportion -= v
    if player_color == PlayerColor.RED:
        return red_proportion
    else:
        return -1 * red_proportion

def get_straight_line_distance(r_x, r_y, b_x, b_y) -> int:
    """
    Gets the minimum number of 1-token spreads needed for red to go to blue,
    including the mirroring distances
    ASSUMPTION: blue is a straight line distance away from red and vice versa
    """
    candidate_value: int = (
        abs(r_x - b_x) if r_x != b_x
        else abs(r_y - b_y)
    )

    if candidate_value >= 4:
        # we want it to revert
        return 7 - candidate_value
    return candidate_value

def same_relative_row(x1, y1, x2, y2):
    """
    Check if two coordinates are on the same vertical or diagonal hex line.
    """
    # If on the same diagonal row
    if x1 == x2 or y1 == y2:
        return True
        # return (x1-x2, y1-y2)
    
    # Without considering mod 7, if on same vertical row
    elif (math.floor((x1 - x2)/6) == -1 and math.ceil((y1 - y2)/6) == 1):
        return True
        # return (-1, 1)
    
    elif (math.floor((x1 - x2)/6) == 1 and math.ceil((y1 - y2)/6) == -1):
        return True
        # return (1, -1)
    return False


def power_within_reach_heuristic(red_tokens, blue_tokens, player_color):
    # Swap if different color
    if player_color == PlayerColor.BLUE:
        intermediate = red_tokens
        red_tokens = blue_tokens
        blue_tokens = intermediate

    within_reach = 0
    for (b_x, b_y), (b_c, b_v) in blue_tokens.items():
        for (r_x, r_y), (r_c, r_v) in red_tokens.items():
            if same_relative_row(r_x, r_y, b_x, b_y):
                if r_v >= get_straight_line_distance(r_x, r_y, b_x, b_y):
                    within_reach += b_v
                    break
    return within_reach

def minimum_move_estimation(board):
    """
    Our heuristic function, given a board position, compute the estimated moves left 
    to reach a goal node. Inadmmisible because of a few edge cases however, we argue, it still
    results in an optimal solution.
    """
    estimate = 0

    # Seperate blue and red tokens for efficiency
    blue_board = {(b_x, b_y): (b_c, b_v) for (b_x, b_y), (b_c, b_v) in board.items() if b_c == "b"}
    red_board = {(r_x, r_y): (r_c, r_v) for (r_x, r_y), (r_c, r_v) in board.items() if r_c == "r"}
    
    for (b_x, b_y), (b_c, b_v) in blue_board.items():
        blue_taken = False
        for (r_x, r_y), (r_c, r_v) in red_board.items():
            # If a blue and red token are on the same straight line and
            # the red token stack can reach the blue token with one spread
            # we estimate that it takes 1 move for the blue token to be captured
            if same_relative_row(r_x, r_y, b_x, b_y):
                if r_v >= get_straight_line_distance(r_x, r_y, b_x, b_y):
                    estimate += 1
                    blue_taken = True
                    break
        
        # If there is no red token on a straight line with a blue token,
        # It takes a higher estimated 1.5 moves.
        if not blue_taken:
            estimate += 1.5
        
        # An additional penalty is calculated and subtracted form the estimate
        # to make the heuristic admissible with respect to most test cases as is possible
        # that blues on a straight line can be captured in 1 move
        for (b_x2, b_y2), (b_c2, b_v2) in blue_board.items():
            if same_relative_row(b_x, b_y, b_x2, b_y2) and (b_x, b_y) != (b_x2, b_y2):
                estimate -= 0.5
                break
 
    return estimate