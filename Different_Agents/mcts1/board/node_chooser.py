"""
The place to implement heuristic-like functions
"""
from enum import Enum
from typing import Generator, List, Optional, Tuple
from random import shuffle, choice
from mcts1.typedefs import BoardDict, BoardKey, ColorChar
from referee.game.actions import Action, SpawnAction, SpreadAction
from referee.game.hex import HexDir, HexPos
from referee.game.player import PlayerColor

ALL_HEX_DIRS = [e.value for e in HexDir]

def generate_action(board, color: PlayerColor) -> Generator[Action, None, None]:
    """
    Generates the next action based on the current state of the board
    """
    # TODO: Make a function that decides the action to take by assessing the
    #       state of the board
    # TODO: Implement the action to take
    _, opponent_tokens, opponent_points, player_tokens, player_points \
            = extract_data(board, color)
    color_char: ColorChar = 'r' \
            if color == PlayerColor.RED \
            else 'b'
    action_choice = assess_board(board, player_tokens, color_char, opponent_tokens)
    if type(action_choice) == Action: 
        yield action_choice # type: ignore

    if action_choice == ActionChoice.SPREAD_DOMINATE:
        # Find the spread that occupies most opponent tokens
        for spread in make_spreads_generator(board, player_tokens, color_char):
            yield spread

    # Assumption: No better choice can be found, its time to choose randomly
    rand_choices = []
    for r in range(7):
        for q in range(7):
            if (r,q) not in board.board_dict:
                rand_choices.append((r,q))
    shuffle(rand_choices)
    if len(rand_choices) == 0 or opponent_points + player_points >= 49:
        pl_token_list = list(player_tokens)
        shuffle(pl_token_list)
        for i in pl_token_list:
            r, q = i
            direction = choice(list(HexDir))
            yield SpreadAction(HexPos(r, q), direction)
    while len(rand_choices) > 1:
        r, q = rand_choices.pop()
        yield SpawnAction(HexPos(r, q))

    r, q = rand_choices.pop()
    yield SpawnAction(HexPos(r, q))

def make_spreads_generator(board, player_tokens, color_char) -> Generator[Action, None, None]:
    """
    Generates a set of spreads that can be dynamically yielded
    """
    spreads_list = get_spreads_list(board, player_tokens, color_char)
    spreads_list.sort(key=lambda x: x[1])
    while len(spreads_list) > 1:
        curr_spread, _ = spreads_list.pop(0)
        yield curr_spread
    curr_spread, _ = spreads_list.pop(0)
    yield curr_spread

def get_spreads_list(board, player_tokens, color_char) \
        -> List[Tuple[SpreadAction, int]]:
    """
    Finds a list of Tuples. Each tuple represents a spread action and how many
    opponent_tokens it can overtake
    """
    finlist = []
    for (pl_key, pl_val) in player_tokens.items():
        pl_r, pl_q = pl_key
        for hex_r, hex_q in ALL_HEX_DIRS:
            current_dir: HexDir = HexDir.Up
            for k in HexDir:
                if k.value.r == hex_r and k.value.q == hex_q:
                    current_dir = k
            num_overtaken = 0
            candidate_spawn: BoardKey = (0, 0)
            for spread_amount in range(1, pl_val[1] + 1):
                candidate_spawn = (
                    (pl_r + spread_amount * hex_r) % 7,
                    (pl_q + spread_amount * hex_q) % 7
                )
                if candidate_spawn not in board.board_dict:
                    continue
                candidate_color, power = board.board_dict[candidate_spawn]
                if candidate_color != color_char:
                    num_overtaken += power
                # num_overtaken += int(candidate_color != color_char)
            if num_overtaken > 0:
                finlist.append(
                    (SpreadAction(
                        HexPos(
                            pl_r,
                            pl_q),
                        current_dir),
                     num_overtaken)
                )
    return finlist

class ActionChoice(Enum):
    """
    Classifiers type(action_choice) == Actionfor  what action can be taken
    """
    # For when a spread in any direction can overtake any opponent token
    SPREAD_DOMINATE = object()

    # For when you can spawn a safe distance away from any opponent node
    SAFE_SPAWN = object()

    # For when you can spawn to your neighbors
    NEIGHBOUR_SPAWN = object()

    # For when there is nothing better to do
    RANDOM_SPAWN = object()

def assess_board(board, player_tokens, color_char, opponent_tokens) -> ActionChoice | Action:
    """
    Decides what action must be taken
    """
    if can_dominate(player_tokens, board, color_char):
        return ActionChoice.SPREAD_DOMINATE
    can_safe_spawn, spawn_value = check_can_safe_spawn(board, opponent_tokens)
    if can_safe_spawn:
        assert spawn_value is not None
        return spawn_value

    can_neighbor_spawn, spawn_value = check_can_neighbor_spawn(board, opponent_tokens)
    if can_neighbor_spawn:
        assert spawn_value is not None
        return spawn_value
    return ActionChoice.RANDOM_SPAWN

def can_dominate(player_tokens: BoardDict, board, color_char: ColorChar) -> bool:
    """
    Checks whether ActionChoice.SPREAD_DOMINATE is a viable strategy
    """
    for (pl_key, pl_val) in player_tokens.items():
        pl_r, pl_q = pl_key
        for hex_r, hex_q in ALL_HEX_DIRS:
            # Check if a spread in that direction can overtake any opponent token
            for spread_amount in range(1, pl_val[1] + 1):
                candidate_spawn: BoardKey = (
                    (pl_r + spread_amount * hex_r) % 7,
                    (pl_q + spread_amount * hex_q) % 7
                )
                if candidate_spawn not in board.board_dict:
                    continue
                candidate_color, _ = board.board_dict[candidate_spawn]
                if candidate_color != color_char:
                    return True
    return False

def check_can_safe_spawn(board, opponent_tokens: BoardDict) \
        -> Tuple[bool, Optional[SpawnAction]]:
    """
    Checks if A safe spawn is possible
    A "safe spawn" would be a spawn that is safely far away from any opponent's
    spread
    """
    for (op_key, op_val) in opponent_tokens.items():
        op_r, op_q = op_key
        spread_amount = op_val[1] + 1
        for hex_r, hex_q in ALL_HEX_DIRS:
            # Check if a spread in that direction can overtake any opponent token
            candidate_spawn: BoardKey = (
                (op_r + spread_amount * hex_r) % 7,
                (op_q + spread_amount * hex_q) % 7
            )

            if candidate_spawn not in board.board_dict:
                return (
                    True,
                    SpawnAction(HexPos(candidate_spawn[0], candidate_spawn[1]))
                )
    return False, None

def check_can_neighbor_spawn(board, player_tokens: BoardDict) \
        -> Tuple[bool, Optional[SpawnAction]]:
    """
    Checks if A safe spawn is possible
    A "safe spawn" would be a spawn that is safely far away from any opponent's
    spread
    """
    for (pl_key, _) in player_tokens.items():
        pl_r, pl_q = pl_key
        for hex_r, hex_q in ALL_HEX_DIRS:
            # Check if a spread in that direction can overtake any opponent token
            candidate_spawn: BoardKey = (
                (pl_r + hex_r) % 7,
                (pl_q + hex_q) % 7
            )

            if candidate_spawn not in board.board_dict:
                return (
                    True,
                    SpawnAction(HexPos(candidate_spawn[0], candidate_spawn[1]))
                )
    return False, None

def choose_naive(board, color: PlayerColor) -> Generator[Action, None, Action]:
    """
    Chooses a naive action to make based on a simple 'common sense' choice,
    pretending like that is the 'expert knowledge'
    """
    opponent_color, opponent_tokens, _, _, _  = extract_data(board, color)

    for (key, _) in opponent_tokens.items():
        # Opponent token coordinates
        op_r, op_q = key
        for hex_r, hex_q in ALL_HEX_DIRS:
            candidate_spawn: BoardKey = (
                (op_r + 2*hex_r) % 7,
                (op_q + 2*hex_q) % 7
            )
            if candidate_spawn in board.board_dict:
                continue

            if __beside_opponent(candidate_spawn, board, opponent_color):
                continue

            new_r, new_q = candidate_spawn
            yield SpawnAction(HexPos(new_r, new_q))
    raise RuntimeError("You were not supposed to reach here")

def extract_data(board, color: PlayerColor):
    """
    Extracts the opponent's data from the player's data
    """
    opponent_color: ColorChar
    player_points, opponent_points = 0, 0
    match color:
        case PlayerColor.RED:
            opponent_color = 'b'
        case PlayerColor.BLUE:
            opponent_color = 'r'
    opponent_tokens: BoardDict = {}
    player_tokens: BoardDict = {}
    curr_dict: BoardDict = board.board_dict
    for (key, value) in curr_dict.items():
        found_color: ColorChar = value[0]
        if found_color == opponent_color:
            opponent_tokens[key] = value
            opponent_points += value[1]
        else:
            player_tokens[key] = value
            player_points += value[1]
    return opponent_color, opponent_tokens, opponent_points, \
           player_tokens, player_points

def __beside_opponent(candidate_spawn, board, opponent_color) -> bool:
    """
    Checks if the current candidate_spawn piece is beside any of the current
    player's opponent pieces
    """
    new_r, new_q = candidate_spawn
    for hex_r, hex_q in ALL_HEX_DIRS:
        new_r, new_q = candidate_spawn
        suspect_tile = (new_r+hex_r, new_q+hex_q)
        if suspect_tile in board.board_dict:
            if board.board_dict[suspect_tile][0] == opponent_color:
                return True
    return False
