from ghost_api.types import Move, Player, Position


def test_get_game_200(service, api_client):
    """
    GET /game/{room_code} OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1")
    service.add_player("ABCD", player1)
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
        "players": [{"name": "player1"}],
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
        "turnPlayerName": "player1",
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
        "players": [],
        "moves": [],
        "turnPlayerName": None,
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


def test_post_move_200(service, api_client):
    """
    POST /game/{room_code}/move OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1")
    player2 = Player(name="player2")
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
    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "players": [{"name": "player1"}, {"name": "player2"}],
        "moves": [new_move_json],
        "turnPlayerName": "player2",
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


def test_post_move_409(service, api_client):
    """
    POST /game/{room_code}/move
    for a player other than the turn player
    """
    service.create_game("ABCD")
    player1 = Player(name="player1")
    player2 = Player(name="player2")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

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
    assert "Turn player is 'player1' but 'player2' tried to move"


def test_post_player_200(service, api_client):
    """
    POST /game/{room_code}/player OK
    """
    service.create_game("ABCD")
    response = api_client.post("/game/ABCD/player", json={"name": "player1"})

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "players": [{"name": "player1"}],
        "moves": [],
        "turnPlayerName": "player1",
    }


def test_post_player_404(service, api_client):
    """
    POST /game/{room_code}/player
    for a nonexistent game
    """
    response = api_client.post("/game/ABCD/player", json={"name": "player1"})

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}


def test_delete_player_200(service, api_client):
    """
    DELETE /game/{room_code}/player OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1")
    player2 = Player(name="player2")
    service.add_player("ABCD", player1)
    service.add_player("ABCD", player2)

    response = api_client.delete("/game/ABCD/player/player1")

    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "players": [{"name": "player2"}],
        "moves": [],
        "turnPlayerName": "player2",
    }


def test_delete_player_404(service, api_client):
    """
    DELETE /game/{room_code}/player
    for a nonexistent game
    """
    response = api_client.delete("/game/ABCD/player/player1")

    assert response.status_code == 404
    assert response.json() == {"message": "Game 'ABCD' does not exist"}
