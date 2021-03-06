import hashlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_camelcase import CamelModel
from mangum import Mangum

from ghost_api.exceptions import (
    GameAlreadyExists,
    GameDoesNotExist,
    GameNotStarted,
    GameStarted,
    InvalidMove,
    WrongPlayer,
)
from ghost_api.logging import get_logger
from ghost_api.service import GhostService
from ghost_api.types import (
    ChallengeResponse,
    ChallengeVote,
    GameInfo,
    GuestLogin,
    Move,
    NewChallenge,
    Player,
)

logger = get_logger()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ErrorMessage(CamelModel):
    """An error message with additional content"""

    message: str


@app.post("/login/guest", response_model=Player)
async def login_guest(info: GuestLogin):
    """
    Simple guest login that generates a display picture
    """
    name_hash = hashlib.md5(info.name.encode()).hexdigest()
    return Player(
        name=info.name,
        image_url=f"https://www.gravatar.com/avatar/{name_hash}?d=identicon",
    )


@app.get(
    "/game/{room_code}",
    response_model=GameInfo,
    responses={404: {"model": ErrorMessage, "description": "The game does not exist"}},
)
async def get_game_info(room_code: str):
    """
    Get game info of an existing game
    """
    logger.info("GET game/%s", room_code)

    service = GhostService()
    try:
        return service.read_game(room_code)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}",
    response_model=GameInfo,
    status_code=201,
    responses={409: {"model": ErrorMessage, "description": "The game already exists"}},
)
async def new_game(room_code: str):
    """
    Create a new game
    """
    logger.info("POST game/%s", room_code)

    service = GhostService()
    try:
        return service.create_game(room_code)
    except GameAlreadyExists as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


@app.delete("/game/{room_code}")
async def delete_game(room_code: str) -> None:
    """
    Delete an existing game, so a new game can be started with the same room
    code
    """
    logger.info("DELETE game/%s", room_code)

    service = GhostService()
    service.delete_game(room_code)


@app.post(
    "/game/{room_code}/start",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
    },
)
async def start_game(room_code: str):
    """
    Start a game, if it's not started
    """
    logger.info("POST /game/%s/start", room_code)

    service = GhostService()
    try:
        return service.start_game(room_code)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}/move",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {
            "model": ErrorMessage,
            "description": "The player can't post a move right now",
        },
    },
)
async def post_new_move(room_code: str, move: Move):
    """
    Make a move in an existing game
    """
    logger.info("POST game/%s/move: %s", room_code, move.dict())

    service = GhostService()
    try:
        return service.add_move(room_code, move)
    except WrongPlayer as e:
        return JSONResponse(status_code=409, content={"message": str(e)})
    except InvalidMove as e:
        return JSONResponse(status_code=409, content={"message": str(e)})
    except GameNotStarted as e:
        return JSONResponse(status_code=409, content={"message": str(e)})
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}/player",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {
            "model": ErrorMessage,
            "description": "The player can't join right now",
        },
    },
)
async def join_game(room_code: str, player: Player):
    """
    Join an existing game
    """
    logger.info("POST game/%s/player: %s", room_code, player.dict())

    service = GhostService()
    try:
        return service.add_player(room_code, player)
    except GameStarted as e:
        return JSONResponse(status_code=409, content={"message": str(e)})
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.delete(
    "/game/{room_code}/player/{player_name}",
    response_model=GameInfo,
    responses={404: {"model": ErrorMessage, "description": "The game does not exist"}},
)
async def remove_player(room_code: str, player_name: str):
    """
    Remove a player from a game
    """
    logger.info("DELETE game/%s/player/%s", room_code, player_name)

    service = GhostService()
    try:
        return service.remove_player(room_code, player_name)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}/challenge",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {
            "model": ErrorMessage,
            "description": "The player can't this challenge right now",
        },
    },
)
async def create_challenge(room_code: str, challenge: NewChallenge):
    """
    Create a challenge on the most recent move
    """
    logger.info("POST /game/%s/challenge: %s", room_code, challenge.dict())

    service = GhostService()
    try:
        return service.create_challenge(room_code, challenge)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})
    except InvalidMove as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


@app.post(
    "/game/{room_code}/challenge-response",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {
            "model": ErrorMessage,
            "description": "The player can't respond to this challenge right now",
        },
    },
)
async def create_challenge_response(
    room_code: str,
    challenge_response: ChallengeResponse,
):
    """
    Respond to an existing challenge with valid words for the given row and
    column
    """
    # TODO: responding player in the header to validate it's being sent by the
    # right person
    logger.info(
        "POST /game/%s/challenge-response: %s", room_code, challenge_response.dict()
    )

    service = GhostService()
    try:
        return service.create_challenge_response(room_code, challenge_response)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})
    except InvalidMove as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


@app.post(
    "/game/{room_code}/challenge-vote",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {
            "model": ErrorMessage,
            "description": "The player can't submit this vote right now",
        },
    },
)
async def add_challenge_vote(room_code: str, vote: ChallengeVote):
    logger.info("POST /game/%s/challenge-vote: %s", room_code, vote.dict())

    service = GhostService()
    try:
        return service.add_challenge_vote(room_code, vote)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})
    except InvalidMove as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


#: Handler for optional serverless deployment of FastAPI app
handler = Mangum(app)
