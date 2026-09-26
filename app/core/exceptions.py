from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(status_code=status_code, detail=detail)


def bad_request(detail: str) -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, detail)


def unauthorized(detail: str = "Could not validate credentials") -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, detail)


def not_found(detail: str = "Resource not found") -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, detail)


def conflict(detail: str) -> AppError:
    return AppError(status.HTTP_409_CONFLICT, detail)
