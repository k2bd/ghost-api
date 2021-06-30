class GhostServiceException(Exception):
    """Base exception for Ghost DB service exceptions"""


class GameDoesNotExist(GhostServiceException):
    """Attempted to read a game that does not exist"""


class GameAlreadyExists(GhostServiceException):
    """Attempted to create a game that already exists"""


class WrongPlayer(GhostServiceException):
    """A player other than the turn player attempted to make a move"""


class PlayerNotJoined(GhostServiceException):
    """Attempted to remove a player who wasn't in the game"""


class InvalidMove(GhostServiceException):
    """A challenge made is not valid"""
