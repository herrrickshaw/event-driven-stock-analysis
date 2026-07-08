"""
Custom exception definitions and error handling.
"""
from fastapi import HTTPException, status


class APIError(HTTPException):
    """Base API error."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "An error occurred",
    ):
        super().__init__(status_code=status_code, detail=detail)


class PortfolioNotFoundError(APIError):
    """Portfolio not found."""

    def __init__(self, portfolio_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio with id {portfolio_id} not found",
        )


class HoldingNotFoundError(APIError):
    """Holding not found."""

    def __init__(self, holding_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding with id {holding_id} not found",
        )


class ValidationError(APIError):
    """Validation error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class InvalidWeightsError(ValidationError):
    """Invalid portfolio weights."""

    def __init__(self):
        super().__init__(detail="Portfolio weights must sum to 100%")


class InsufficientDataError(APIError):
    """Insufficient data for calculation."""

    def __init__(self, detail: str = "Insufficient data for requested calculation"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class DatabaseError(APIError):
    """Database operation error."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


class ExternalServiceError(APIError):
    """External service (yfinance, etc.) error."""

    def __init__(self, service: str, detail: str = None):
        message = f"Error fetching data from {service}"
        if detail:
            message += f": {detail}"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message,
        )


class CalculationError(APIError):
    """Error during metric calculation."""

    def __init__(self, metric: str, detail: str = None):
        message = f"Error calculating {metric}"
        if detail:
            message += f": {detail}"
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )
