import boto3

from ghost_api.constants import AWS_REGION, LOCAL_DYNAMODB_ENDPOINT, GAMES_TABLE_NAME
from ghost_api.types import GameInfo, Move, Player
from typing import Generator, Dict, Any


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


class GhostService:
    def __init__(self):
        self.db = dynamodb()
        self.games_table = self.db.Table(GAMES_TABLE_NAME)

    def create_game(self) -> GameInfo:
        """
        Create a new game in the database

        Raises
        ------
        TODO
        """

    def read_game(self) -> GameInfo:
        """
        Read a game state from the database

        Raises
        ------
        TODO
        """

    def add_move(self, room_code: str, new_move: Move) -> GameInfo:
        """
        Play a new move if it's made by the turn player, also updating the turn
        player.

        Raises
        ------
        TODO
        """

    def add_player(self, room_code, new_player: Player) -> GameInfo:
        """
        Add a player to a game, if they're not already in the game

        Raises
        ------
        TODO
        """

    def delete_game(self, room_code: str) -> None:
        """
        Remove a game in the database if it exists
        """
