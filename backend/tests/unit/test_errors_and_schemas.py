"""Unit tests for utils/errors.py status codes and messages."""
import pytest

from utils.errors import (
    CalculationError,
    ExternalServiceError,
    HoldingNotFoundError,
    InsufficientDataError,
    InvalidWeightsError,
    PortfolioNotFoundError,
)


@pytest.mark.unit
@pytest.mark.parametrize("exc,code,fragment", [
    (PortfolioNotFoundError(7), 404, "Portfolio with id 7 not found"),
    (HoldingNotFoundError(3), 404, "Holding with id 3 not found"),
    (InvalidWeightsError(), 422, "sum to 100%"),
    (InsufficientDataError(), 400, "Insufficient data"),
])
def test_error_status_and_detail(exc, code, fragment):
    assert exc.status_code == code and fragment in exc.detail


@pytest.mark.unit
def test_service_and_calculation_errors_name_their_source():
    assert "yfinance" in ExternalServiceError("yfinance").detail
    assert "VaR" in CalculationError("VaR").detail
