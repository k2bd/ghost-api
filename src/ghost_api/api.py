from fastapi import FastAPI
from mangum import Mangum
from fastapi_camelcase import CamelModel
from fastapi.responses import JSONResponse

from ghost_api.types import GameInfo, Move, Player

app = FastAPI()

class ErrorMessage(CamelModel):
    message: str


@app.get("/game/{gameId}")
async def get_game_info(gameId: str) -> GameInfo:
    """
    Get game info of an existing game
    """
    ...


@app.delete("/game/{gameId}")
async def delete_game(gameId: str) -> None:
    """
    Delete an existing game, so a new game can be started with the same room
    code
    """
    ...


@app.post("/game/{gameId}/move", responses={409: {"model": ErrorMessage}})
async def post_new_move(gameId: str, move: Move) -> GameInfo:
    """
    Make a move in a game, creating it if it doesn't exist
    """
    ...


@app.post("/game/{gameId}/join", responses={409: {"model": ErrorMessage}})
async def post_new_move(gameId: str, player: Player) -> GameInfo:
    """
    Join a game, creating it if it doesn't exist
    """
    ...


#: Handler for serverless deployment of FastAPI app
handler = Mangum(app)
