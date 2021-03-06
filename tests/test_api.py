from ghost_api.types import ChallengeType, Move, NewChallenge, Player, Position


def test_get_game_200(service, api_client):
    """
    GET /game/{room_code} OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="abc.def")
    player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)
    service.start_game("ABCD")
    move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="K",
    )
    service.add_move("ABCD", move)

    response = api_client.get("/game/ABCD")
    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abc.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [
            {
                "playerName": "player1",
                "position": {
                    "x": 0,
                    "y": 0,
                },
                "letter": "K",
            }
        ],
        "turnPlayerName": "player2",
        "challenge": None,
        "losers": [],
    }


def test_get_game_404(service, api_client):
    """
    GET /game/{room_code}
    for nonexistent room
    """
    response = api_client.get("/game/ABCD")
    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_game_201(service, api_client):
    """
    POST /game/{room_code} OK
    """
    response = api_client.post("/game/ABCD")
    assert response.status_code == 201
    assert response.json() == {
        "roomCode": "ABCD",
        "started": False,
        "winner": None,
        "players": [],
        "moves": [],
        "turnPlayerName": None,
        "challenge": None,
        "losers": [],
    }


def test_post_game_409(service, api_client):
    """
    POST /game/{room_code}
    for an already existing game
    """
    service.create_game("ABCD")
    response = api_client.post("/game/ABCD")
    assert response.status_code == 409
    assert response.json() == {"message": "Game 'ABCD' already exists"}


def test_delete_game_200_exists(service, api_client):
    """
    DELETE /game/{room_code}
    for an existing game
    """
    service.create_game("ABCD")
    response = api_client.delete("/game/ABCD")
    assert response.status_code == 200


def test_delete_game_200_not_exists(service, api_client):
    """
    DELETE /game/{room_code}
    for a nonexistent game
    """
    response = api_client.delete("/game/ABCD")
    assert response.status_code == 200


def test_post_start_game_200(service, api_client):
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="abc.def")
    player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    response = api_client.post("/game/ABCD/start")
    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abc.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [],
        "turnPlayerName": "player1",
        "challenge": None,
        "losers": [],
    }


def test_post_start_game_404(service, api_client):
    response = api_client.post("/game/ABCD/start")
    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_move_200(service, api_client):
    """
    POST /game/{room_code}/move OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="abc.def")
    player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }

    response = api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )
    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abc.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [new_move_json],
        "turnPlayerName": "player2",
        "challenge": None,
        "losers": [],
    }


def test_post_move_404(service, api_client):
    """
    POST /game/{room_code}/move
    for a nonexistent game
    """
    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    response = api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )
    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_move_409_wrong_player(service, api_client):
    """
    POST /game/{room_code}/move
    for a player other than the turn player
    """
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="abc.def")
    player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player2",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }

    response = api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )
    assert response.status_code == 409
    assert response.json() == {
        "message": "Turn player is 'player1' but 'player2' tried to move"
    }


def test_post_move_409_pending_challenge(service, api_client):
    """
    POST /game/{room_code}/move
    when there's an existing challenge
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abc.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move = Move(
        player_name="player1",
        position=Position(x=0, y=0),
        letter="U",
    )
    service.add_move("ABCD", new_move)

    challenge = NewChallenge(
        challenger_name="player2",
        move=new_move,
        type=ChallengeType.NO_VALID_WORDS,
    )
    service.create_challenge("ABCD", challenge)

    new_move_json = {
        "playerName": "player2",
        "position": {
            "x": 0,
            "y": 1,
        },
        "letter": "P",
    }

    response = api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )
    assert response.status_code == 409
    assert response.json() == {"message": "Game 'ABCD' has an open challenge"}


def test_post_move_409_not_started(service, api_client):
    """
    POST /game/{room_code}/move 409
    Game hasn't started
    """
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="abc.def")
    player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }

    response = api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )
    assert response.status_code == 409
    assert response.json() == {
        "message": "Cannot make a move in a game that hasn't started"
    }


def test_post_player_200(service, api_client):
    """
    POST /game/{room_code}/player OK
    """
    service.create_game("ABCD")
    response = api_client.post(
        "/game/ABCD/player", json={"name": "player1", "imageUrl": "abc.def"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": False,
        "winner": None,
        "players": [{"name": "player1", "imageUrl": "abc.def"}],
        "moves": [],
        "turnPlayerName": "player1",
        "challenge": None,
        "losers": [],
    }


def test_post_player_404(service, api_client):
    """
    POST /game/{room_code}/player
    for a nonexistent game
    """
    response = api_client.post(
        "/game/ABCD/player", json={"name": "player1", "imageUrl": "abc.def"}
    )

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_player_409(service, api_client):
    """
    POST /game/{room_code}/player 409
    Game has already started
    """
    service.create_game("ABCD")
    service.start_game("ABCD")
    response = api_client.post(
        "/game/ABCD/player", json={"name": "player1", "imageUrl": "abc.def"}
    )

    assert response.status_code == 409
    assert response.json() == {"message": "Cannot join a game that's started"}


def test_delete_player_200(service, api_client):
    """
    DELETE /game/{room_code}/player OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1", image_url="aaaa.aaa")
    player2 = Player(name="player2", image_url="abc.def")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    response = api_client.delete("/game/ABCD/player/player1")

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": False,
        "winner": None,
        "players": [{"name": "player2", "imageUrl": "abc.def"}],
        "moves": [],
        "turnPlayerName": "player2",
        "challenge": None,
        "losers": [],
    }


def test_delete_player_404(service, api_client):
    """
    DELETE /game/{room_code}/player
    for a nonexistent game
    """
    response = api_client.delete("/game/ABCD/player/player1")

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_challenge_200(service, api_client):
    """
    POST /game/{room_code}/challenge OK
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "NO_VALID_WORDS",
    }
    response = api_client.post("/game/ABCD/challenge", json=new_challenge)

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abd.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [new_move_json],
        "turnPlayerName": "player1",
        "challenge": {
            **new_challenge,
            "state": "AWAITING_RESPONSE",
            "response": None,
            "votes": [],
        },
        "losers": [],
    }


def test_post_challenge_404(service, api_client):
    """
    POST /game/{room_code}/challenge
    For a nonexistent game
    """
    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "NO_VALID_WORDS",
    }
    response = api_client.post("/game/ABCD/challenge", json=new_challenge)

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_challenge_409(service, api_client):
    """
    POST /game/{room_code}/challenge
    With an invalid challenge
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": {
            "playerName": "player1",
            "position": {
                "x": 5,  # Invlid challenge - the move isn't right
                "y": 5,
            },
            "letter": "U",
        },
        "type": "NO_VALID_WORDS",
    }
    response = api_client.post("/game/ABCD/challenge", json=new_challenge)

    assert response.status_code == 409
    assert response.json() == {"message": "Can only challenge the most recent move"}


def test_post_challenge_response_200(service, api_client):
    """
    POST /game/{room_code}/challenge-response OK
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "NO_VALID_WORDS",
    }
    api_client.post("/game/ABCD/challenge", json=new_challenge)

    challenge_response = {
        "rowWord": "UMBRELLA",
        "colWord": "UPPER",
    }
    response = api_client.post("/game/ABCD/challenge-response", json=challenge_response)

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abd.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [new_move_json],
        "turnPlayerName": "player1",
        "challenge": {
            **new_challenge,
            "state": "VOTING",
            "response": challenge_response,
            "votes": [],
        },
        "losers": [],
    }


def test_post_challenge_response_404(service, api_client):
    """
    POST /game/{room_code}/challenge-response
    For a nonexistent game
    """
    challenge_response = {
        "rowWord": "UMBRELLA",
        "colWord": "UPPER",
    }
    response = api_client.post("/game/ABCD/challenge-response", json=challenge_response)

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_challenge_response_409(service, api_client):
    """
    POST /game/{room_code}/challenge-response
    With an invalid response
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "COMPLETE_WORD",
    }
    api_client.post("/game/ABCD/challenge", json=new_challenge)

    challenge_response = {
        "rowWord": "UMBRELLA",
        "colWord": "UPPER",
    }
    response = api_client.post("/game/ABCD/challenge-response", json=challenge_response)

    assert response.status_code == 409
    assert response.json() == {
        "message": "Challenge is in 'VOTING' state, not 'AWAITING_RESPONSE'"
    }


def test_post_challenge_vote_200(service, api_client):
    """
    POST /game/{room_code}/challenge-vote OK
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "COMPLETE_WORD",
    }
    api_client.post("/game/ABCD/challenge", json=new_challenge)

    challenge_vote = {
        "voterName": "player1",
        "proChallenge": False,
    }
    response = api_client.post("/game/ABCD/challenge-vote", json=challenge_vote)

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "started": True,
        "winner": None,
        "players": [
            {"name": "player1", "imageUrl": "abd.def"},
            {"name": "player2", "imageUrl": "ghi.jkl"},
        ],
        "moves": [new_move_json],
        "turnPlayerName": "player1",
        "challenge": {
            **new_challenge,
            "state": "VOTING",
            "response": None,
            "votes": [challenge_vote],
        },
        "losers": [],
    }


def test_post_challenge_vote_404(service, api_client):
    """
    POST /game/{room_code}/challenge-vote
    For a nonexistent game
    """
    challenge_vote = {
        "voterName": "player1",
        "proChallenge": False,
    }
    response = api_client.post("/game/ABCD/challenge-vote", json=challenge_vote)

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_post_challenge_vote_409(service, api_client):
    """
    POST /game/{room_code}/challenge-vote
    With an invalid vote
    """
    service.create_game("ABCD")

    new_player1 = Player(name="player1", image_url="abd.def")
    service.add_player("ABCD", new_player1)
    new_player2 = Player(name="player2", image_url="ghi.jkl")
    service.add_player("ABCD", new_player2)

    service.start_game("ABCD")

    new_move_json = {
        "playerName": "player1",
        "position": {
            "x": 0,
            "y": 0,
        },
        "letter": "U",
    }
    api_client.post(
        "/game/ABCD/move",
        json=new_move_json,
    )

    new_challenge = {
        "challengerName": "player2",
        "move": new_move_json,
        "type": "NO_VALID_WORDS",
    }
    api_client.post("/game/ABCD/challenge", json=new_challenge)

    challenge_vote = {
        "voterName": "player1",
        "proChallenge": False,
    }
    response = api_client.post("/game/ABCD/challenge-vote", json=challenge_vote)

    assert response.status_code == 409
    assert response.json() == {
        "message": "Challenge is in 'AWAITING_RESPONSE' state, not 'VOTING'"
    }
