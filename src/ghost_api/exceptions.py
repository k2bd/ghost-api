class GhostServiceException(Exception):
    """ Base exception for Ghost DB service exceptions """


class GameDoesNotExist(Exception):
    """ Attempted to read a game that does not exist """


class GameAlreadyExists(Exception):
    """ Attempted to create a game that already exists """


class WrongPlayerMoved(Exception):
    """ A player other than the turn player attempted to make a move """


class PlayerNotJoined(Exception):
    """ Attempted to remove a player who wasn't in the game """
