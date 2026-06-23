from fastapi import HTTPException, status


class DuplicateResourceError(HTTPException):
    def __init__(self, detail: str = "Resource already exists or violates a unique constraint.") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class IngestionValidationError(HTTPException):
    def __init__(self, detail: str, attempts: int) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": detail, "healing_attempts": attempts},
        )
