from fastapi import HTTPException, status


class DuplicateResourceError(HTTPException):
    def __init__(self, detail: str = "Resource already exists or violates a unique constraint.") -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)
