from ghost_api.types import Player, Move


def test_get_game_200(service, api_client):
    """
    GET /game/{room_code} OK
    """
    service.create_game("ABCD")
    player1 = Player(name="player1")
    service.add_player("ABCD", player1)
    move = Move(
        player_name="player1",
        position_x=0,
        position_y=0,
        letter="K",
    )
    service.add_move("ABCD", move)

    response = api_client.get("/game/ABCD")
    assert response.status_code == 200
    assert response.json() == {
        "roomCode": "ABCD",
        "players": [
            {"name": "player1"}
        ],
        "moves": [
            {
                "playerName": "player1",
                "positionX": 0,
                "positionY": 0,
                "letter": "K",
            }
        ],
        "turnPlayerName": "player1",
    }
