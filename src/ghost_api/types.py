from typing import List, Tuple

from fastapi_camelcase import CamelModel


class Player(CamelModel):
    #: Player display name
    name: str


class Move(CamelModel):
    #: Player that made the move
    player: Player

    #: 0-indexed (x, y) position of the move
    position: Tuple[int, int]

    #: Letter played
    letter: str


class GameInfo(CamelModel):
    #: Room Code
    room_code: str

    #: Players, in move order
    players: List[Player]

    #: Current turn player
    current_turn: Player

    #: Moves made so far, in play order
    moves_made: List[Move]
