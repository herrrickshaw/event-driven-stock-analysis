"""Service layer: constructor wiring, DB-backed portfolio lookups, and the
contract that every not-yet-implemented method fails loudly with
NotImplementedError rather than returning a silent placeholder."""

import pytest

from config.settings import settings
from services import (
    AlertEngineService,
    PortfolioAnalyzerService,
    RebalancingEngineService,
    ReportingService,
    RiskCalculatorService,
)


@pytest.mark.unit
def test_risk_calculator_snapshots_settings(db_session, monkeypatch):
    monkeypatch.setattr(settings, "risk_free_rate", 0.07)
    monkeypatch.setattr(settings, "confidence_level", 0.99)
    monkeypatch.setattr(settings, "lookback_period", 60)
    svc = RiskCalculatorService(db_session)
    assert svc.db is db_session
    assert (svc.risk_free_rate, svc.confidence_level, svc.lookback_period) == (0.07, 0.99, 60)


@pytest.mark.unit
@pytest.mark.parametrize(
    "cls", [AlertEngineService, ReportingService, RebalancingEngineService, PortfolioAnalyzerService]
)
def test_services_hold_the_session(cls, db_session):
    assert cls(db_session).db is db_session


STUBBED = [
    (PortfolioAnalyzerService, "get_portfolio_snapshot", (1,)),
    (PortfolioAnalyzerService, "calculate_returns", (1, "1y")),
    (PortfolioAnalyzerService, "compare_with_benchmark", (1, "SPY")),
    (RiskCalculatorService, "calculate_volatility", (1,)),
    (RiskCalculatorService, "calculate_var", (1, 0.99, "1w")),
    (RiskCalculatorService, "calculate_correlations", (1,)),
    (RiskCalculatorService, "calculate_exposure", (1,)),
    (RiskCalculatorService, "calculate_beta", (1, "SPY")),
    (RiskCalculatorService, "calculate_sharpe_ratio", (1,)),
    (AlertEngineService, "get_alert_status", (1,)),
    (AlertEngineService, "trigger_alerts", (1, ["drift"])),
    (AlertEngineService, "check_drift_alert", (1,)),
    (AlertEngineService, "check_volatility_alert", (1,)),
    (AlertEngineService, "check_correlation_alert", (1,)),
    (AlertEngineService, "check_loss_alert", (1,)),
    (AlertEngineService, "check_concentration_alert", (1,)),
    (AlertEngineService, "acknowledge_alert", (1,)),
    (AlertEngineService, "create_alert", (1, "drift", 5.0)),
    (RebalancingEngineService, "schedule_rebalancing", (1, "annual", {"A": 100.0})),
    (RebalancingEngineService, "calculate_drift", (1, 5.0)),
    (RebalancingEngineService, "execute_rebalancing", (1,)),
    (RebalancingEngineService, "get_rebalance_actions", (1, {"A": 100.0})),
    (RebalancingEngineService, "estimate_rebalancing_costs", (1, [])),
    (ReportingService, "generate_daily_report", (1,)),
    (ReportingService, "generate_monthly_report", (1, "2024-01")),
    (ReportingService, "calculate_daily_performance", (1,)),
    (ReportingService, "calculate_monthly_performance", (1, "2024-01")),
    (ReportingService, "identify_top_movers", (1, 3)),
    (ReportingService, "calculate_sector_performance", (1,)),
    (ReportingService, "save_report_to_db", (1, "daily", {})),
    (ReportingService, "get_report_history", (1, "daily", 5)),
]


@pytest.mark.unit
@pytest.mark.parametrize("cls,method,args", STUBBED, ids=lambda v: getattr(v, "__name__", None) or None)
def test_unimplemented_methods_raise(cls, method, args, db_session):
    with pytest.raises(NotImplementedError, match="not implemented"):
        getattr(cls(db_session), method)(*args)


@pytest.mark.unit
def test_optional_arguments_have_expected_defaults(db_session):
    import inspect

    sig = inspect.signature
    assert sig(PortfolioAnalyzerService.calculate_returns).parameters["period"].default == "1d"
    var = sig(RiskCalculatorService.calculate_var).parameters
    assert (var["confidence_level"].default, var["time_horizon"].default) == (0.95, "1d")
    assert sig(RebalancingEngineService.calculate_drift).parameters["drift_threshold_pct"].default == 5.0
    assert sig(ReportingService.identify_top_movers).parameters["top_n"].default == 5
    assert sig(ReportingService.get_report_history).parameters["limit"].default == 10


@pytest.mark.unit
class TestPortfolioLookups:
    def test_get_portfolio_by_id_hit_and_miss(self, db_session, sample_portfolio):
        svc = PortfolioAnalyzerService(db_session)
        assert svc.get_portfolio_by_id(sample_portfolio.id).name == "Test Portfolio"
        assert svc.get_portfolio_by_id(sample_portfolio.id + 1) is None

    def test_list_holdings_filters_by_portfolio(self, db_session, sample_portfolio):
        from models import Holding, Portfolio

        other = Portfolio(name="Other", user_id="u2")
        db_session.add(other)
        db_session.commit()
        for pid, sym in ((sample_portfolio.id, "AAA"), (sample_portfolio.id, "BBB"), (other.id, "CCC")):
            db_session.add(
                Holding(portfolio_id=pid, symbol=sym, market="us", quantity=1, purchase_price=1, current_price=1)
            )
        db_session.commit()
        svc = PortfolioAnalyzerService(db_session)
        assert sorted(h.symbol for h in svc.list_holdings(sample_portfolio.id)) == ["AAA", "BBB"]
        assert [h.symbol for h in svc.list_holdings(other.id)] == ["CCC"]
        assert svc.list_holdings(999) == []
