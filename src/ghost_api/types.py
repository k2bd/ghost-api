from typing import List, Optional, Tuple

from fastapi_camelcase import CamelModel


class Player(CamelModel):
    #: Player display name
    name: str


class Move(CamelModel):
    #: Player that made the move
    player: Player

    #: 0-indexed x-position of the move
    position_x: int

    #: 0-indexed y-position of the move
    position_y: int

    #: Letter played
    letter: str


class GameInfo(CamelModel):
    #: Room Code
    room_code: str

    #: Players, in move order
    players: List[Player]

    #: Current turn player name
    turn_player_name: Optional[str]

    #: Moves made so far, in play order
    moves: List[Move]
