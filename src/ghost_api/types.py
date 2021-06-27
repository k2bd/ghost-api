from enum import Enum
from typing import List, Optional

from fastapi_camelcase import CamelModel


class Player(CamelModel):
    #: Player display name
    name: str


class Position(CamelModel):
    #: 0-indexed x-position of the move
    x: int

    #: 0-indexed y-position of the move
    y: int


class Move(CamelModel):
    #: Player that made the move
    player_name: str

    #: Postion of the move
    position: Position

    #: Letter played
    letter: str


class ChallengeType(Enum, str):
    #: Challenged move completed a word in its row or column
    COMPLETE_WORD = "COMPLETE_WORD"

    #: It is not possible to create a word in the challenged move's row or
    #: column
    NO_VALID_WORDS = "NO_VALID_WORDS"


class ChallengeState(Enum, str):
    #: Challenge awaiting a response
    AWAIATING_RESPONSE = "AWAIATING_RESPONSE"

    #: Challenge waiting for votes to come in
    VOTING = "VOTING"

    #: Challenge successful
    SUCCESS = "SUCCESS"

    #: Challenge failed
    FAILED = "FAILED"


class ChallengeResponse(CamelModel):
    #: Valid word in the row
    row_word: str

    #: Valid word in the column
    col_word: str


class ChallengeVote(CamelModel):
    #: Player that cast the vote
    voter_name: str

    #: If the vote is in favour of the challenge
    pro_challenge: bool


class NewChallenge(CamelModel):
    """
    Challenge info to be posted by the user
    """

    #: Player issuing the challenge
    challenger_name: str

    #: Move being challenged
    move: Move

    #: Type of challenge
    type: ChallengeType


class Challenge(NewChallenge):
    #: Current state of the challenge
    state: ChallengeState

    #: Response, if received
    response: Optional[ChallengeResponse]

    #: Votes cast, if received
    votes: List[ChallengeVote]


class GameInfo(CamelModel):
    #: Room Code
    room_code: str

    #: Players, in move order
    players: List[Player]

    #: Current turn player name
    turn_player_name: Optional[str]

    #: Moves made so far, in play order
    moves: List[Move]

    #: Any currently active challenge
    challenge: Optional[Challenge]
