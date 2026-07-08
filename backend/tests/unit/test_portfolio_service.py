"""
Unit tests for portfolio analyzer service.
"""
import pytest
from services import PortfolioAnalyzerService


@pytest.mark.unit
class TestPortfolioAnalyzerService:
    """Portfolio analyzer service tests."""

    def test_get_portfolio_by_id(self, db_session, sample_portfolio):
        """Test fetching portfolio by ID."""
        service = PortfolioAnalyzerService(db_session)
        portfolio = service.get_portfolio_by_id(sample_portfolio.id)

        assert portfolio is not None
        assert portfolio.id == sample_portfolio.id
        assert portfolio.name == "Test Portfolio"

    def test_get_portfolio_not_found(self, db_session):
        """Test fetching non-existent portfolio."""
        service = PortfolioAnalyzerService(db_session)
        portfolio = service.get_portfolio_by_id(9999)

        assert portfolio is None

    def test_list_holdings(self, db_session, sample_portfolio, sample_holdings):
        """Test listing portfolio holdings."""
        service = PortfolioAnalyzerService(db_session)
        holdings = service.list_holdings(sample_portfolio.id)

        assert len(holdings) == 2
        assert holdings[0].symbol in ["AAPL", "GOOGL"]
        assert holdings[1].symbol in ["AAPL", "GOOGL"]

    def test_list_holdings_empty(self, db_session, sample_portfolio):
        """Test listing holdings for empty portfolio."""
        service = PortfolioAnalyzerService(db_session)
        holdings = service.list_holdings(sample_portfolio.id)

        assert len(holdings) == 0

    # TODO: Implement tests for portfolio snapshot calculation
    # def test_get_portfolio_snapshot(self, db_session, sample_portfolio, sample_holdings):
    #     """Test portfolio snapshot calculation."""
    #     service = PortfolioAnalyzerService(db_session)
    #     snapshot = service.get_portfolio_snapshot(sample_portfolio.id)
    #
    #     assert snapshot.portfolio_id == sample_portfolio.id
    #     assert snapshot.total_value > 0
    #     assert snapshot.total_return > 0

    # TODO: Implement tests for returns calculation
    # def test_calculate_returns(self, db_session, sample_portfolio):
    #     """Test returns calculation."""
    #     service = PortfolioAnalyzerService(db_session)
    #     returns = service.calculate_returns(sample_portfolio.id, period="1d")
    #
    #     assert returns.portfolio_id == sample_portfolio.id
    #     assert returns.period == "1d"

    # TODO: Implement tests for benchmark comparison
    # def test_compare_with_benchmark(self, db_session, sample_portfolio):
    #     """Test benchmark comparison."""
    #     service = PortfolioAnalyzerService(db_session)
    #     comparison = service.compare_with_benchmark(sample_portfolio.id, "^GSPC")
    #
    #     assert comparison.portfolio_id == sample_portfolio.id
    #     assert comparison.benchmark_symbol == "^GSPC"
