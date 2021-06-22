from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_camelcase import CamelModel
from mangum import Mangum

from ghost_api.exceptions import GameAlreadyExists, GameDoesNotExist, WrongPlayerMoved
from ghost_api.logging import get_logger
from ghost_api.service import GhostService
from ghost_api.types import GameInfo, Move, Player

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
    "/game/{room_code}/move",
    response_model=GameInfo,
    responses={
        404: {"model": ErrorMessage, "description": "The game does not exist"},
        409: {"model": ErrorMessage, "description": "It's not this player's turn"},
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
    except WrongPlayerMoved as e:
        return JSONResponse(status_code=409, content={"message": str(e)})
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}/player",
    response_model=GameInfo,
    responses={404: {"model": ErrorMessage, "description": "The game does not exist"}},
)
async def join_game(room_code: str, player: Player):
    """
    Join an existing game
    """
    logger.info("POST game/%s/player: %s", room_code, player.dict())

    service = GhostService()
    try:
        return service.add_player(room_code, player)
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


#: Handler for optional serverless deployment of FastAPI app
handler = Mangum(app)
