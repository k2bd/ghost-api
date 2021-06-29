import pytest

from ghost_api.exceptions import (
    GameAlreadyExists,
    GameDoesNotExist,
    InvalidMove,
    WrongPlayer,
)
from ghost_api.types import (
    Challenge,
    ChallengeResponse,
    ChallengeState,
    ChallengeType,
    GameInfo,
    Move,
    NewChallenge,
    Player,
    Position,
)


def test_create_game(service):
    """
    A new game is created successfully
    """
    game = service.create_game("ABCD")

    assert game == GameInfo(
        room_code="ABCD",
        players=[],
        turn_player_name=None,
        moves=[],
    )


def test_create_game_already_exists(service):
    """
    Creating an already existing game raises an error
    """
    service.create_game("ABCD")

    with pytest.raises(GameAlreadyExists):
        service.create_game("ABCD")


def test_read_game(service):
    """
    We can read created games
    """
    service.create_game("ABCD")
    read_game = service.read_game("ABCD")

    assert read_game == GameInfo(
        room_code="ABCD",
        players=[],
        turn_player_name=None,
        moves=[],
    )


def test_read_nonexistent_game(service):
    """
    Can't read a game that doesn't exist
    """
    with pytest.raises(GameDoesNotExist):
        service.read_game("ABCD")


def test_delete_game(service):
    """
    Deleting a game removes it from the database
    """
    service.create_game("BCDE")

    service.delete_game("BCDE")

    with pytest.raises(GameDoesNotExist):
        service.read_game("BCDE")


def test_delete_game_idempotent(service):
    """
    Deleting a nonexistent game is fine
    """
    service.delete_game("AABB")  # Game doesn't exist


def test_add_player(service):
    """
    We can add players to a game, which also initializes the turn player
    """
    service.create_game("AAAA")

    new_player = Player(name="player1")
    service.add_player("AAAA", new_player)

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player]
    assert read_game.turn_player_name == "player1"


def test_add_players(service):
    """
    New players appear at the end of the list, which does not advance the turn
    player
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="another_player")
    service.add_player("AAAA", new_player2)

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player1, new_player2]
    assert read_game.turn_player_name == "player1"


def test_add_player_idempotent(service):
    """
    Adding a player that's already in the game does not create a duplicate
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player1")
    service.add_player("AAAA", new_player2)

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player1]
    assert read_game.turn_player_name == "player1"


def test_add_move(service):
    """
    The turn player can make a move
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move1 = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="Z",
    )

    service.add_move("AAAA", new_move1)

    read_game = service.read_game("AAAA")
    assert read_game.moves == [new_move1]
    assert read_game.turn_player_name == "player2"

    new_move2 = Move(
        player_name="player2",
        position=Position(x=0, y=1),
        letter="U",
    )

    service.add_move("AAAA", new_move2)

    read_game = service.read_game("AAAA")
    assert read_game.moves == [new_move1, new_move2]
    assert read_game.turn_player_name == "player1"


def test_add_move_wrong_player(service):
    """
    Whoever isn't the turn player cannot make a move
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player2",
        position=Position(x=0, y=0),
        letter="U",
    )

    with pytest.raises(WrongPlayer):
        service.add_move("AAAA", new_move)

    read_game = service.read_game("AAAA")
    assert read_game.moves == []
    assert read_game.turn_player_name == "player1"


def test_add_move_empty_game(service):
    """
    Nobody can move if there's nobody joined
    """
    service.create_game("AAAA")

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )

    with pytest.raises(WrongPlayer):
        service.add_move("AAAA", new_move)

    read_game = service.read_game("AAAA")
    assert read_game.moves == []
    assert read_game.turn_player_name is None


def test_add_move_pending_challenge(service):
    """
    Cannot add a move when there's a pending challenge
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    service.create_challenge("AAAA", challenge)

    #: Cannot make a move while there's an active challenge
    invalid_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    with pytest.raises(InvalidMove):
        service.add_move("AAAA", invalid_move)


def test_remove_player_turn_player(service):
    """
    Removing the turn player removes them from the players list and passes to
    the next player's turn
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="Z",
    )
    current_game = service.add_move("AAAA", new_move)

    assert current_game.turn_player_name == "player2"

    service.remove_player("AAAA", "player2")

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player1]
    assert read_game.turn_player_name == "player1"


def test_remove_player_other_player(service):
    """
    Removing a player who isn't the turn player removes them from the players
    list
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    current_game = service.add_player("AAAA", new_player2)

    assert current_game.turn_player_name == "player1"

    service.remove_player("AAAA", "player2")

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player1]
    assert read_game.turn_player_name == "player1"


def test_remove_player_only_player(service):
    """
    Removing the only player resets the turn player to None
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)

    service.remove_player("AAAA", "player1")

    read_game = service.read_game("AAAA")
    assert read_game.players == []
    assert read_game.turn_player_name is None


def test_remove_player_nonexistent_player(service):
    """
    Removing the only player resets the turn player to None
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)

    service.remove_player("AAAA", "player2")

    read_game = service.read_game("AAAA")
    assert read_game.players == [new_player1]
    assert read_game.turn_player_name == "player1"


def test_create_challenge(service):
    """
    Can create a new challenge if there's been a move
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    service.create_challenge("AAAA", challenge)

    expected_challenge = Challenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
        state=ChallengeState.AWAITING_RESPONSE,
        response=None,
        votes=[],
    )

    read_game = service.read_game("AAAA")
    assert read_game.challenge == expected_challenge


def test_create_challenge_second_challenge(service):
    """
    Cannot create a challenge when there's already a pending challenge
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)
    new_player3 = Player(name="player3")
    service.add_player("AAAA", new_player3)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    service.create_challenge("AAAA", challenge)

    second_challenge = NewChallenge(
        challenger_name="player3",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    with pytest.raises(InvalidMove):
        service.create_challenge("AAAA", second_challenge)

    expected_challenge = Challenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
        state=ChallengeState.AWAITING_RESPONSE,
        response=None,
        votes=[],
    )
    read_game = service.read_game("AAAA")
    assert read_game.challenge == expected_challenge


def test_create_challenge_invalid_player(service):
    """
    A player that isn't joined can't make a challenge
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge = NewChallenge(
        challenger_name="player5",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    with pytest.raises(InvalidMove):
        service.create_challenge("AAAA", challenge)


def test_create_challenge_previous_moves(service):
    """
    Can't challenge a move that isn't the most recent
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)
    new_player2 = Player(name="player3")
    service.add_player("AAAA", new_player2)

    first_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", first_move)

    second_move = Move(
        player_name="player2",
        position=Position(x=1, y=0),
        letter="P",
    )
    service.add_move("AAAA", second_move)

    challenge = NewChallenge(
        challenger_name="player3",
        move=first_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    with pytest.raises(InvalidMove):
        service.create_challenge("AAAA", challenge)


def test_create_challenge_no_moves(service):
    """
    Can't challenge in a game with no moves
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    challenge_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    challenge = NewChallenge(
        challenger_name="player1",
        move=challenge_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    with pytest.raises(InvalidMove):
        service.create_challenge("AAAA", challenge)


def test_create_challenge_response(service):
    """
    Can submit a response to an active AWAITING_RESPONSE challenge
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    service.create_challenge("AAAA", challenge)

    challenge_response = ChallengeResponse(
        row_word="UMBRELLA",
        col_word="UPPER",
    )
    service.create_challenge_response("AAAA", challenge_response)

    expected_challenge = Challenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
        state=ChallengeState.VOTING,
        response=challenge_response,
        votes=[],
    )

    read_game = service.read_game("AAAA")
    assert read_game.challenge == expected_challenge


def test_create_challenge_response_no_challenge(service):
    """
    Cannot respond to a challenge if the game doesn't have an active challenge
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    challenge_response = ChallengeResponse(
        row_word="UMBRELLA",
        col_word="UPPER",
    )
    with pytest.raises(InvalidMove):
        service.create_challenge_response("AAAA", challenge_response)


def test_create_challenge_response_wrong_state(service):
    """
    Cannot respond to a challenge not in the AWAITING_RESPONSE state
    """
    service.create_game("AAAA")

    new_player1 = Player(name="player1")
    service.add_player("AAAA", new_player1)
    new_player2 = Player(name="player2")
    service.add_player("AAAA", new_player2)

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("AAAA", new_move)

    # COMPLETE_WORD does not require a response - goes right to voting
    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.COMPLETE_WORD,
    )
    service.create_challenge("AAAA", challenge)

    challenge_response = ChallengeResponse(
        row_word="UMBRELLA",
        col_word="UPPER",
    )
    with pytest.raises(InvalidMove):
        service.create_challenge_response("AAAA", challenge_response)
