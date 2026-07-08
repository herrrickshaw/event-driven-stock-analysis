"""
Integration tests for portfolio endpoints.
"""
import pytest


@pytest.mark.integration
class TestPortfolioEndpoints:
    """Portfolio endpoint tests."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data

    # TODO: Implement endpoint tests when endpoints are implemented

    # def test_get_portfolio_snapshot(self, client, sample_portfolio):
    #     """Test portfolio snapshot endpoint."""
    #     response = client.post(
    #         f"/api/portfolio/snapshot?portfolio_id={sample_portfolio.id}"
    #     )
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["portfolio_id"] == sample_portfolio.id
    #     assert "total_value" in data

    # def test_get_portfolio_returns(self, client, sample_portfolio):
    #     """Test portfolio returns endpoint."""
    #     response = client.post(
    #         f"/api/portfolio/returns?portfolio_id={sample_portfolio.id}&period=1d"
    #     )
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["portfolio_id"] == sample_portfolio.id
    #     assert data["period"] == "1d"

    # def test_compare_with_benchmark(self, client, sample_portfolio):
    #     """Test benchmark comparison endpoint."""
    #     response = client.post(
    #         f"/api/portfolio/benchmark?portfolio_id={sample_portfolio.id}&benchmark_symbol=^GSPC"
    #     )
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["portfolio_id"] == sample_portfolio.id
    #     assert data["benchmark_symbol"] == "^GSPC"

    # def test_get_portfolio_not_found(self, client):
    #     """Test portfolio not found error."""
    #     response = client.post("/api/portfolio/snapshot?portfolio_id=9999")
    #     assert response.status_code == 404
    #     data = response.json()
    #     assert "Portfolio with id 9999 not found" in data["detail"]
