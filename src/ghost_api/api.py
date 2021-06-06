from copy import Error

from botocore import serialize
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi_camelcase import CamelModel
from mangum import Mangum

from ghost_api.exceptions import GameAlreadyExists, GameDoesNotExist, WrongPlayerMoved
from ghost_api.service import GhostService
from ghost_api.types import GameInfo, Move, Player

app = FastAPI()


class ErrorMessage(CamelModel):
    """An error message with additional content"""

    message: str


@app.get("/game/{room_code}", responses={404: {"model": ErrorMessage}})
async def get_game_info(room_code: str) -> GameInfo:
    """
    Get game info of an existing game
    """
    service = GhostService()

    try:
        return service.read_game(room_code)
    except GameDoesNotExist as e:
        return JSONResponse(status_code=404, content={"message": str(e)})


@app.post(
    "/game/{room_code}",
    status_code=201,
    responses={409: {"model": ErrorMessage}},
)
async def new_game(room_code: str) -> GameInfo:
    """
    Create a new game
    """
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
    service = GhostService()
    service.delete_game(room_code)


@app.post("/game/{room_code}/move", responses={409: {"model": ErrorMessage}})
async def post_new_move(room_code: str, move: Move) -> GameInfo:
    """
    Make a move in an existing game
    """
    service = GhostService()

    try:
        return service.add_move(room_code, move)
    except WrongPlayerMoved as e:
        return JSONResponse(status_code=409, content={"message": str(e)})


@app.post("/game/{room_code}/join")
async def join_game(room_code: str, player: Player) -> GameInfo:
    """
    Join an existing game
    """
    service = GhostService()
    return service.add_player(room_code, player)


# TODO: kick player


#: Handler for optional serverless deployment of FastAPI app
handler = Mangum(app)
