import boto3
from boto3.dynamodb.conditions import Attr

from ghost_api.constants import AWS_REGION, GAMES_TABLE_NAME, LOCAL_DYNAMODB_ENDPOINT
from ghost_api.exceptions import (
    GameAlreadyExists,
    GameDoesNotExist,
    InvalidMove,
    WrongPlayer,
)
from ghost_api.types import (
    Challenge,
    ChallengeState,
    ChallengeType,
    GameInfo,
    Move,
    NewChallenge,
    Player,
)


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
        turn_player_name=None,
        moves=[],
        challenge=None,
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
            self.read_game(room_code)
        except GameDoesNotExist:
            self.games_table.put_item(Item=dict(new_game(room_code)))
        else:
            raise GameAlreadyExists(f"Game {room_code!r} already exists")

        return self.read_game(room_code)

    def read_game(self, room_code: str) -> GameInfo:
        """
        Read a game state from the database

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        """
        response = self.games_table.get_item(Key={"room_code": room_code})

        if "Item" not in response:
            raise GameDoesNotExist(f"Game {room_code!r} does not exist")

        return GameInfo.parse_obj(response["Item"])

    def delete_game(self, room_code: str) -> None:
        """
        Remove a game in the database if it exists
        """
        self.games_table.delete_item(Key={"room_code": room_code})

    def add_player(self, room_code: str, new_player: Player) -> GameInfo:
        """
        Add a player to a game, if they're not already in the game

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        """
        game = self.read_game(room_code)

        if new_player.name in [player.name for player in game.players]:
            return game

        # If this is the first player to join the game, initialize the turn player
        turn_player_name = (
            game.turn_player_name
            if game.turn_player_name is not None
            else new_player.name
        )

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=(
                "set turn_player_name=:t, players=list_append(players, :p)"
            ),
            ExpressionAttributeValues={
                ":p": [new_player.dict()],
                ":t": turn_player_name,
            },
            ConditionExpression=Attr("players").eq(game.dict()["players"]),
        )
        return self.read_game(room_code)

    def remove_player(self, room_code: str, player_name: str) -> GameInfo:
        """
        Remove a player from the game, updating the turn player if necessary.
        """
        game = self.read_game(room_code)
        new_player_list = game.players.copy()

        matched_players = [
            player for player in game.players if player.name == player_name
        ]
        if len(matched_players) == 0:
            return game
        (player,) = matched_players

        new_player_list.remove(player)

        turn_player_name = game.turn_player_name
        if turn_player_name == player.name:
            # Pass to the next player
            player_index = game.players.index(player)
            if len(new_player_list) == 0:
                turn_player_name = None
            else:
                turn_player = new_player_list[player_index % len(new_player_list)]
                turn_player_name = turn_player.name

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set turn_player_name=:t, players=:p"),
            ExpressionAttributeValues={
                ":t": turn_player_name,
                ":p": [player.dict() for player in new_player_list],
            },
            ConditionExpression=Attr("players").eq(game.dict()["players"]),
        )

        return self.read_game(room_code)

    def add_move(self, room_code: str, new_move: Move) -> GameInfo:
        """
        Play a new move if it's made by the turn player, also updating the turn
        player.

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        WrongPlayer
            If a player other than the turn player is making the move
        InvalidMove
            If the move cannot be made
        """
        game = self.read_game(room_code)

        if game.challenge is not None:
            raise InvalidMove(f"Game {room_code!r} has an open challenge")

        if game.turn_player_name != new_move.player_name:
            msg = "Turn player is {!r} but {!r} tried to move"
            raise WrongPlayer(msg.format(game.turn_player_name, new_move.player_name))

        # TODO: validate move position and value

        player_indexes = {player.name: ind for ind, player in enumerate(game.players)}
        new_player_ind = (player_indexes[new_move.player_name] + 1) % len(game.players)
        new_player_name = game.players[new_player_ind].name

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set turn_player_name=:p, moves=list_append(moves, :m)"),
            ExpressionAttributeValues={
                ":p": new_player_name,
                ":m": [new_move.dict()],
            },
            ConditionExpression=Attr("moves").eq(game.dict()["moves"]),
        )
        return self.read_game(room_code)

    def create_challenge(
        self,
        room_code: str,
        challenge: NewChallenge,
    ) -> GameInfo:
        """
        Create a new challenge of a given move

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        InvalidMove
            If the challenge cannot be made
        """
        game = self.read_game(room_code)

        if game.challenge is not None:
            raise InvalidMove(f"Game {room_code!r} already has an open challenge")

        if challenge.challenger_name not in [player.name for player in game.players]:
            msg = f"Player {challenge.challenger_name!r} not in game {room_code!r}"
            raise InvalidMove(msg)

        if (len(game.moves) == 0) or (challenge.move != game.moves[-1]):
            raise InvalidMove("Can only challenge the most recent move")

        initial_state = (
            ChallengeState.AWAITING_RESPONSE
            if challenge.type is ChallengeType.NO_VALID_WORDS
            else ChallengeState.VOTING
        )

        game_challenge = Challenge(
            challenger_name=challenge.challenger_name,
            move=challenge.move,
            type=challenge.type,
            state=initial_state,
            response=None,
            votes=[],
        )

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set challenge=:c"),
            ExpressionAttributeValues={":c": game_challenge.dict()},
            ConditionExpression=Attr("challenge").eq(None),
        )

        return self.read_game(room_code)
