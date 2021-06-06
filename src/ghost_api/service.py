import boto3

from ghost_api.constants import AWS_REGION, LOCAL_DYNAMODB_ENDPOINT, GAMES_TABLE_NAME
from ghost_api.types import GameInfo, Move, Player
from typing import Generator, Dict, Any, Optional
from ghost_api.exceptions import GameAlreadyExists, GameDoesNotExist


def dynamodb():
    config = {}
    if LOCAL_DYNAMODB_ENDPOINT is not None:
        config["endpoint_url"] = LOCAL_DYNAMODB_ENDPOINT
    elif AWS_REGION is not None:
        config["region_name"] = AWS_REGION
    else:
        msg = "Please set either AWS_REGION or LOCAL_DYNAMODB_ENDPOINT"
        raise EnvironmentError(msg)

    return boto3.resource("dynamodb", **config)


def new_game(room_code: str) -> GameInfo:
    return GameInfo(
        room_code=room_code,
        players=[],
        current_turn=None,
        moves_made=[],
    )


class GhostService:
    def __init__(self):
        self.db = dynamodb()
        self.games_table = self.db.Table(GAMES_TABLE_NAME)

    def create_game(self, room_code: str) -> GameInfo:
        """
        Create a new game in the database

        Raises
        ------
        GameAlreadyExists
            If the game already exists
        """
        try:
            existing_game = self.read_game(room_code)
            raise GameAlreadyExists(f"Game {room_code!r} already exists: {existing_game!r}")
        except GameDoesNotExist:
            self.games_table.put_item(Item=new_game(room_code))

        return self.read_game(room_code)

    def read_game(self, room_code: str) -> Optional[GameInfo]:
        """
        Read a game state from the database

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        """
        response = self.games_table.get_item(Key={"roomCode": room_code})

        if "Item" not in response:
            raise GameDoesNotExist(f"Game {room_code!r} does not exist")

        return GameInfo.parse_obj(response["Item"])

    def delete_game(self, room_code: str) -> None:
        """
        Remove a game in the database if it exists
        """
        self.games_table.delete_item(Key={"roomCode": room_code})

    def add_move(self, room_code: str, new_move: Move) -> GameInfo:
        """
        Play a new move if it's made by the turn player, also updating the turn
        player.

        Raises
        ------
        WrongPlayerMoved
            If a player other than the turn player is making the move
        """

    def add_player(self, room_code: str, new_player: Player) -> GameInfo:
        """
        Add a player to a game, if they're not already in the game
        """

    def remove_player(self, room_code: str, player_name: str) -> GameInfo:
        """
        Remove a player from the game, updating the turn player if necessary.
        """
