"""App factory behaviour (handlers, system endpoints, lifecycle) and the
not-yet-implemented DB-backed routes."""

import asyncio
import json

import pytest

from config.settings import settings


@pytest.mark.integration
class TestSystemEndpoints:
    def test_health(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "app": settings.app_name, "version": settings.app_version}

    def test_root(self, client):
        assert client.get("/").json() == {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "openapi": "/openapi.json",
        }

    def test_unknown_route_404(self, client):
        assert client.get("/nope").status_code == 404

    def test_cors_allows_configured_origin(self, client):
        r = client.get("/api/health", headers={"Origin": settings.cors_origins[0]})
        assert r.headers["access-control-allow-origin"] == settings.cors_origins[0]
        r = client.get("/api/health", headers={"Origin": "http://evil.example"})
        assert "access-control-allow-origin" not in r.headers

    def test_lifecycle_events_run_without_error(self, client):
        with client:  # triggers startup + shutdown handlers
            assert client.get("/api/health").status_code == 200

    def test_all_routers_registered_once_without_double_prefix(self, client):
        paths = [r.path for r in client.app.routes]
        for p in (
            "/api/portfolio/snapshot",
            "/api/risk/var",
            "/api/rebalance/drift",
            "/api/alerts/stream",
            "/api/reports/monthly",
        ):
            assert paths.count(p) == 1


@pytest.mark.integration
class TestErrorHandlers:
    def test_api_error_includes_path(self, client):
        r = client.post("/api/portfolio/snapshot?portfolio_id=12345")
        assert r.status_code == 404
        assert r.json() == {"detail": "Portfolio with id 12345 not found", "path": "/api/portfolio/snapshot"}

    @pytest.mark.parametrize(
        "path",
        [
            "/api/risk/volatility?portfolio_id=1",
            "/api/risk/var?portfolio_id=1",
            "/api/risk/correlation?portfolio_id=1",
            "/api/risk/exposure?portfolio_id=1",
            "/api/reports/daily?portfolio_id=1",
            "/api/reports/monthly?portfolio_id=1",
            "/api/reports/monthly?portfolio_id=1&month=2024-01",
            "/api/rebalance/execute?portfolio_id=1",
            "/api/rebalance/execute?portfolio_id=1&dry_run=true",
        ],
    )
    def test_unimplemented_endpoint_is_sanitised_500(self, client, path):
        r = client.post(path)
        assert r.status_code == 500
        assert r.json() == {"detail": "Internal server error", "path": path.split("?")[0]}

    def test_unimplemented_body_endpoints(self, client):
        for path, body in (
            ("/api/alerts/trigger", {"portfolio_id": 1}),
            ("/api/rebalance/drift", {"portfolio_id": 1}),
            (
                "/api/rebalance/schedule",
                {"portfolio_id": 1, "rebalance_type": "annual", "target_weights": {"A": 100.0}},
            ),
        ):
            r = client.post(path, json=body)
            assert r.status_code == 500 and r.json()["detail"] == "Internal server error"

    def test_alert_status_unimplemented(self, client):
        assert client.post("/api/alerts/status?portfolio_id=1").status_code == 500


@pytest.mark.integration
class TestParameterValidation:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/portfolio/snapshot?portfolio_id=0",
            "/api/portfolio/snapshot",
            "/api/portfolio/returns?portfolio_id=0",
            "/api/portfolio/benchmark?portfolio_id=1",
            "/api/portfolio/benchmark?portfolio_id=1&benchmark_symbol=",
            "/api/risk/volatility?portfolio_id=1&lookback_days=29",
            "/api/risk/correlation?portfolio_id=1&lookback_days=29",
            "/api/risk/var?portfolio_id=0",
            "/api/risk/exposure?portfolio_id=-1",
            "/api/rebalance/execute?portfolio_id=0",
            "/api/reports/daily?portfolio_id=0",
            "/api/alerts/status?portfolio_id=0",
        ],
    )
    def test_rejected_with_422(self, client, path):
        assert client.post(path).status_code == 422

    def test_lookback_boundary_30_accepted_by_validation(self, client):
        # 30 passes validation and reaches the (unimplemented) handler -> 500, not 422
        assert client.post("/api/risk/volatility?portfolio_id=1&lookback_days=30").status_code == 500
        assert client.post("/api/risk/correlation?portfolio_id=1&lookback_days=30").status_code == 500

    def test_body_validation(self, client):
        assert client.post("/api/rebalance/drift", json={}).status_code == 422
        assert client.post("/api/alerts/trigger", json={}).status_code == 422
        assert client.post("/api/rebalance/schedule", json={"portfolio_id": 1}).status_code == 422


@pytest.mark.integration
class TestPortfolioRoutesWithExistingPortfolio:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/portfolio/snapshot?portfolio_id={id}",
            "/api/portfolio/returns?portfolio_id={id}",
            "/api/portfolio/returns?portfolio_id={id}&period=5y",
            "/api/portfolio/benchmark?portfolio_id={id}&benchmark_symbol=SPY",
        ],
    )
    def test_existing_portfolio_reaches_unimplemented_body(self, client, sample_portfolio, path):
        r = client.post(path.format(id=sample_portfolio.id))
        assert r.status_code == 500 and r.json()["detail"] == "Internal server error"

    @pytest.mark.parametrize(
        "path",
        [
            "/api/portfolio/returns?portfolio_id=777",
            "/api/portfolio/benchmark?portfolio_id=777&benchmark_symbol=SPY",
        ],
    )
    def test_missing_portfolio_404(self, client, path):
        r = client.post(path)
        assert r.status_code == 404 and "777" in r.json()["detail"]


@pytest.mark.integration
class TestSSEStream:
    def test_subscribe_sse_formats_events_and_unsubscribes(self, monkeypatch):
        import routers.alerts as alerts
        from events.event_bus import EventBus, MarketEvent

        bus = EventBus()
        monkeypatch.setattr(alerts, "bus", bus)

        async def scenario():
            gen = alerts.subscribe_sse()
            first = asyncio.ensure_future(gen.__anext__())
            await asyncio.sleep(0)  # let the generator subscribe
            assert len(bus._subscribers["*"]) == 1
            await bus.publish(MarketEvent(type="RSI_CROSS", ticker="TCS", market="india", data={"rsi": 71}))
            chunk = await first
            await gen.aclose()
            return chunk

        chunk = asyncio.run(scenario())
        head, data, blank = chunk.split("\n", 2)[0], chunk.split("\n")[1], chunk.endswith("\n\n")
        assert head == "event: RSI_CROSS" and blank
        payload = json.loads(data[len("data: ") :])
        assert payload["event_type"] == "RSI_CROSS" and payload["ticker"] == "TCS"
        assert payload["market"] == "india" and payload["data"] == {"rsi": 71}
        assert payload["timestamp"].startswith("20")
        assert bus._subscribers["*"] == []  # finally: unsubscribed

    def test_events_delivered_in_publish_order(self, monkeypatch):
        import routers.alerts as alerts
        from events.event_bus import EventBus, MarketEvent

        bus = EventBus()
        monkeypatch.setattr(alerts, "bus", bus)

        async def scenario():
            gen = alerts.subscribe_sse()
            t = asyncio.ensure_future(gen.__anext__())
            await asyncio.sleep(0)
            for tk in ("A", "B"):
                await bus.publish(MarketEvent(type="X", ticker=tk, market="us"))
            out = [await t, await gen.__anext__()]
            await gen.aclose()
            return out

        out = asyncio.run(scenario())
        assert [json.loads(c.split("data: ")[1])["ticker"] for c in out] == ["A", "B"]

    def test_stream_endpoint_is_event_stream(self, monkeypatch):
        import routers.alerts as alerts

        resp = asyncio.run(alerts.stream_alerts())
        assert resp.media_type == "text/event-stream"


@pytest.mark.integration
def test_get_alerts_limit_and_order(monkeypatch):
    import routers.alerts as alerts
    from events.event_bus import EventBus, MarketEvent

    bus = EventBus()
    monkeypatch.setattr(alerts, "bus", bus)
    for i in range(5):
        asyncio.run(bus.publish(MarketEvent(type="T", ticker=f"S{i}", market="us", data={"i": i})))
    assert [a["ticker"] for a in alerts.get_alerts(2)] == ["S4", "S3"]
    assert [a["ticker"] for a in alerts.get_alerts()] == ["S4", "S3", "S2", "S1", "S0"]
    assert alerts.get_alerts(1)[0]["data"] == {"i": 4}
