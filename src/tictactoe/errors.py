class DomainError(Exception):
    pass


class InvalidPositionError(DomainError):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(f"invalid position ({row}, {column})")


class InvalidPlayerError(DomainError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"invalid player symbol {symbol!r}")


class InvalidBoardError(DomainError):
    def __init__(self) -> None:
        super().__init__("a board must have exactly 9 cells")


class PositionOccupiedError(DomainError):
    def __init__(self, row: int, column: int) -> None:
        super().__init__(f"cell ({row}, {column}) is already occupied")


class GameAlreadyOverError(DomainError):
    def __init__(self, game_id: str) -> None:
        super().__init__(f"game {game_id} is already over")


class GameNotFoundError(DomainError):
    def __init__(self, game_id: str) -> None:
        super().__init__(f"game {game_id} not found")


class GameAlreadyExistsError(DomainError):
    def __init__(self, game_id: str) -> None:
        super().__init__(f"game {game_id} already exists")
