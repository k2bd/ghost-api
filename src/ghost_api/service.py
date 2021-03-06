import boto3
from boto3.dynamodb.conditions import Attr

from ghost_api.constants import AWS_REGION, GAMES_TABLE_NAME, LOCAL_DYNAMODB_ENDPOINT
from ghost_api.exceptions import (
    GameAlreadyExists,
    GameDoesNotExist,
    GameNotStarted,
    GameStarted,
    InvalidMove,
    WrongPlayer,
)
from ghost_api.types import (
    Challenge,
    ChallengeResponse,
    ChallengeState,
    ChallengeType,
    ChallengeVote,
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
        started=False,
        winner=None,
        players=[],
        losers=[],
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

    def read_game(self, room_code: str, consistent=False) -> GameInfo:
        """
        Read a game state from the database

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        """
        response = self.games_table.get_item(
            Key={"room_code": room_code},
            ConsistentRead=consistent,
        )

        if "Item" not in response:
            raise GameDoesNotExist(f"Game {room_code!r} does not exist")

        return GameInfo.parse_obj(response["Item"])

    def delete_game(self, room_code: str) -> None:
        """
        Remove a game in the database if it exists
        """
        self.games_table.delete_item(Key={"room_code": room_code})

    def start_game(self, room_code: str) -> GameInfo:
        """
        Start a game if it isn't already started
        """
        self.read_game(room_code)
        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression="set started=:s",
            ExpressionAttributeValues={":s": True},
        )
        return self.read_game(room_code)

    def add_player(self, room_code: str, new_player: Player) -> GameInfo:
        """
        Add a player to a game, if they're not already in the game

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        GameStarted
            If the game has started so can't be joined
        """
        game = self.read_game(room_code)
        if game.started:
            raise GameStarted("Cannot join a game that's started")

        if new_player.name in [player.name for player in game.players + game.losers]:
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

    def _determine_winner(self, room_code: str) -> None:
        """
        Determine if there's a winner and update the game in the database if so
        """
        game = self.read_game(room_code)
        if (len(game.players) == 1) and game.started:
            (winner,) = game.players
            self.games_table.update_item(
                Key={"room_code": room_code},
                UpdateExpression=("set winner=:p"),
                ExpressionAttributeValues={
                    ":p": winner.dict(),
                },
            )

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

        self._determine_winner(room_code)

        return self.read_game(room_code)

    def _advance_turn(self, game: GameInfo) -> None:
        if game.turn_player_name is None:
            if len(game.players) == 0:
                new_player_name = None
            else:
                new_player_name = game.players[0].name
        else:
            player_indexes = {
                player.name: ind for ind, player in enumerate(game.players)
            }
            new_player_ind = (player_indexes[game.turn_player_name] + 1) % len(
                game.players
            )
            new_player_name = game.players[new_player_ind].name

        self.games_table.update_item(
            Key={"room_code": game.room_code},
            UpdateExpression=("set turn_player_name=:p"),
            ExpressionAttributeValues={
                ":p": new_player_name,
            },
            ConditionExpression=Attr("players").eq(game.dict()["players"]),
        )

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
        GameNotStarted
            If the game hasn't started yet
        """
        game = self.read_game(room_code)
        if not game.started:
            raise GameNotStarted("Cannot make a move in a game that hasn't started")

        if game.challenge is not None:
            raise InvalidMove(f"Game {room_code!r} has an open challenge")

        if game.turn_player_name != new_move.player_name:
            msg = "Turn player is {!r} but {!r} tried to move"
            raise WrongPlayer(msg.format(game.turn_player_name, new_move.player_name))

        if new_move.player_name not in [player.name for player in game.players]:
            raise InvalidMove("Must join a game to play a move")

        if new_move.position in [move.position for move in game.moves]:
            raise InvalidMove(f"There is already a move on {new_move.position.dict()}")

        if len(new_move.letter) != 1:
            raise InvalidMove("Moves can only be one letter")

        # TODO: validate move position and value

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set moves=list_append(moves, :m)"),
            ExpressionAttributeValues={
                ":m": [new_move.dict()],
            },
            ConditionExpression=Attr("moves").eq(game.dict()["moves"]),
        )

        self._advance_turn(game)

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

        self._advance_turn(game)

        return self.read_game(room_code)

    def create_challenge_response(
        self,
        room_code: str,
        challenge_response: ChallengeResponse,
    ) -> GameInfo:
        """
        Respond to a challenge in the AWAITING_RESPONSE state

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        InvalidMove
            If the challenge response is invalid
        """
        game = self.read_game(room_code)

        if game.challenge is None:
            msg = f"No challenge exists on game {room_code!r}"
            raise InvalidMove(msg)
        if game.challenge.state != ChallengeState.AWAITING_RESPONSE:
            state = game.challenge.state.value
            msg = f"Challenge is in {state!r} state, not 'AWAITING_RESPONSE'"
            raise InvalidMove(msg)

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set challenge.#chalresp=:r, challenge.#chalstate=:s"),
            ExpressionAttributeValues={
                ":r": challenge_response.dict(),
                ":s": ChallengeState.VOTING,
            },
            ExpressionAttributeNames={
                # "response" and "state" are reserved words
                "#chalstate": "state",
                "#chalresp": "response",
            },
            ConditionExpression=Attr("challenge").eq(game.dict()["challenge"]),
        )

        return self.read_game(room_code)

    def _complete_challenge(self, game: GameInfo) -> None:
        if game.challenge is None:
            raise ValueError("Cannot complete a nonexistent challenge")
        # All votes in, apply the result
        pro_challenge_votes = [
            vote for vote in game.challenge.votes if vote.pro_challenge
        ]
        if len(pro_challenge_votes) / len(game.challenge.votes) < 0.5:
            loser_name = game.challenge.challenger_name
        else:
            loser_name = game.challenge.move.player_name

        if loser_name == game.turn_player_name:
            self._advance_turn(game)

        remaining_players = [
            player for player in game.players if player.name != loser_name
        ]
        (loser,) = [player for player in game.players if player.name == loser_name]

        self.games_table.update_item(
            Key={"room_code": game.room_code},
            UpdateExpression=(
                "set challenge=:n, players=:p, losers=list_append(losers, :l)"
            ),
            ExpressionAttributeValues={
                ":n": None,
                ":p": [player.dict() for player in remaining_players],
                ":l": [loser.dict()],
            },
            ConditionExpression=(
                Attr("players").eq(game.dict()["players"])
                & Attr("challenge").eq(game.dict()["challenge"])
                & Attr("losers").eq(game.dict()["losers"])
            ),
        )

        self._determine_winner(game.room_code)

    def add_challenge_vote(self, room_code: str, vote: ChallengeVote) -> GameInfo:
        """
        Vote on a challenge in the VOTING stage.

        If everyone's votes are in, kick the loser and continue the game.

        Raises
        ------
        GameDoesNotExist
            If the game doesn't exist
        InvalidMove
            If the vote can't be cast
        """
        game = self.read_game(room_code)

        if game.challenge is None:
            msg = f"No challenge exists on game {room_code!r}"
            raise InvalidMove(msg)
        if game.challenge.state != ChallengeState.VOTING:
            state = game.challenge.state.value
            msg = f"Challenge is in {state!r} state, not 'VOTING'"
            raise InvalidMove(msg)
        if vote.voter_name in [v.voter_name for v in game.challenge.votes]:
            raise InvalidMove(f"Player {vote.voter_name!r} has already voted")
        if vote.voter_name not in [player.name for player in game.players]:
            msg = f"Player {vote.voter_name!r} has not joined game {room_code!r}"
            raise InvalidMove(msg)

        self.games_table.update_item(
            Key={"room_code": room_code},
            UpdateExpression=("set challenge.votes=list_append(challenge.votes, :v)"),
            ExpressionAttributeValues={
                ":v": [vote.dict()],
            },
            ConditionExpression=Attr("challenge").eq(game.dict()["challenge"]),
        )

        game = self.read_game(room_code, consistent=True)

        if game.challenge is not None:
            if len(game.challenge.votes) == len(game.players):
                self._complete_challenge(game)

        return self.read_game(room_code)
