"""Integration tests for the implemented live-watchlist / EventBus endpoints."""
import pytest

from events import event_bus, portfolio_monitor


@pytest.fixture(autouse=True)
def fresh_singletons(monkeypatch):
    bus = event_bus.EventBus()
    mon = portfolio_monitor.PortfolioMonitor()
    import routers.alerts as alerts
    monkeypatch.setattr(alerts, "bus", bus)
    monkeypatch.setattr(alerts, "monitor", mon)
    return bus, mon


@pytest.mark.integration
class TestAlertsWatchlist:
    def test_add_list_remove(self, client):
        r = client.post("/api/alerts/portfolio", json={"tickers": ["RELIANCE", "TCS"]})
        assert r.status_code == 200 and r.json()["watched"] == ["RELIANCE", "TCS"]
        assert client.get("/api/alerts/portfolio").json() == {"watched": ["RELIANCE", "TCS"]}
        assert client.delete("/api/alerts/portfolio/TCS").json() == {"watched": ["RELIANCE"]}

    def test_add_requires_ticker_list(self, client):
        assert client.post("/api/alerts/portfolio", json={"market": "us"}).status_code == 422

    def test_manual_trigger_publishes_and_latest_is_newest_first(self, client, fresh_singletons):
        bus, _ = fresh_singletons
        for t in ("AAA", "BBB", "CCC"):
            assert client.post(f"/api/alerts/trigger/{t}?market=us").json() == {
                "status": "triggered", "ticker": t}
        assert [e.ticker for e in bus.history] == ["AAA", "BBB", "CCC"]
        latest = client.get("/api/alerts/latest?limit=2").json()["alerts"]
        assert [a["ticker"] for a in latest] == ["CCC", "BBB"]
        assert latest[0]["event_type"] == "MANUAL_TRIGGER" and latest[0]["market"] == "us"

    def test_latest_limit_is_validated(self, client):
        assert client.get("/api/alerts/latest?limit=0").status_code == 422
        assert client.get("/api/alerts/latest?limit=501").status_code == 422


@pytest.mark.integration
def test_existing_routes_are_not_double_prefixed(client):
    paths = {r.path for r in client.app.routes}
    assert "/api/alerts/latest" in paths
    assert not any(p.startswith("/api/api/") for p in paths)
