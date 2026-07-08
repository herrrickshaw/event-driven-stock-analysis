"""
Unit tests for risk metrics calculations.

Test cases:
- Volatility (standard deviation of returns)
- Value at Risk (VaR) at 95% and 99% confidence levels
- Correlation matrix
- Beta calculation
- Sharpe ratio
"""
from __future__ import annotations

import math
import statistics
from typing import List

import pytest
import numpy as np


class RiskMetricsCalculator:
    """Utility class for risk calculations."""

    @staticmethod
    def calculate_volatility(returns: List[float]) -> float:
        """Calculate volatility as standard deviation of returns."""
        if len(returns) < 2:
            return 0.0
        return statistics.stdev(returns)

    @staticmethod
    def calculate_annualized_volatility(daily_returns: List[float]) -> float:
        """Convert daily volatility to annualized (multiply by sqrt(252))."""
        daily_vol = RiskMetricsCalculator.calculate_volatility(daily_returns)
        return daily_vol * math.sqrt(252)

    @staticmethod
    def calculate_var_historical(returns: List[float], confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk using historical simulation.
        VaR is the loss that would occur at the given confidence level.

        confidence: 0.95 (95%) or 0.99 (99%)
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return sorted_returns[index]

    @staticmethod
    def calculate_var_parametric(
        mean_return: float,
        volatility: float,
        confidence: float = 0.95,
        portfolio_value: float = 1.0,
    ) -> float:
        """
        Calculate VaR using parametric (normal distribution) method.
        Assumes returns are normally distributed.
        """
        # Z-score for confidence level
        z_scores = {0.95: 1.645, 0.99: 2.326}
        z = z_scores.get(confidence, 1.645)

        var = (mean_return - z * volatility) * portfolio_value
        return var

    @staticmethod
    def calculate_correlation(returns_a: List[float], returns_b: List[float]) -> float:
        """Calculate correlation between two return series."""
        if len(returns_a) != len(returns_b) or len(returns_a) < 2:
            return 0.0

        mean_a = statistics.mean(returns_a)
        mean_b = statistics.mean(returns_b)

        covariance = sum((a - mean_a) * (b - mean_b) for a, b in zip(returns_a, returns_b)) / (
            len(returns_a) - 1
        )
        std_a = statistics.stdev(returns_a)
        std_b = statistics.stdev(returns_b)

        if std_a == 0 or std_b == 0:
            return 0.0

        return covariance / (std_a * std_b)

    @staticmethod
    def calculate_covariance(returns_a: List[float], returns_b: List[float]) -> float:
        """Calculate covariance between two return series."""
        if len(returns_a) != len(returns_b) or len(returns_a) < 2:
            return 0.0

        mean_a = statistics.mean(returns_a)
        mean_b = statistics.mean(returns_b)

        return sum((a - mean_a) * (b - mean_b) for a, b in zip(returns_a, returns_b)) / (
            len(returns_a) - 1
        )

    @staticmethod
    def calculate_beta(
        asset_returns: List[float],
        market_returns: List[float],
    ) -> float:
        """Calculate beta as covariance / market variance."""
        if len(asset_returns) != len(market_returns):
            return 0.0

        covariance = RiskMetricsCalculator.calculate_covariance(asset_returns, market_returns)
        market_variance = statistics.variance(market_returns)

        if market_variance == 0:
            return 0.0

        return covariance / market_variance

    @staticmethod
    def calculate_sharpe_ratio(
        portfolio_return: float,
        portfolio_volatility: float,
        risk_free_rate: float = 0.05,  # 5% annual
    ) -> float:
        """Calculate Sharpe ratio."""
        if portfolio_volatility == 0:
            return 0.0

        excess_return = portfolio_return - risk_free_rate
        return excess_return / portfolio_volatility

    @staticmethod
    def calculate_max_drawdown(returns: List[float]) -> float:
        """Calculate maximum drawdown from peak."""
        if not returns:
            return 0.0

        cumulative = [1.0]
        for r in returns:
            cumulative.append(cumulative[-1] * (1 + r))

        max_value = cumulative[0]
        max_dd = 0.0

        for value in cumulative:
            if value > max_value:
                max_value = value
            dd = (max_value - value) / max_value
            if dd > max_dd:
                max_dd = dd

        return max_dd


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Volatility
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestVolatility:
    """Test volatility calculations."""

    def test_volatility_constant_returns(self):
        """Test volatility when all returns are the same."""
        returns = [0.01] * 100
        vol = RiskMetricsCalculator.calculate_volatility(returns)
        assert vol == 0.0

    def test_volatility_simple(self):
        """Test volatility calculation."""
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        vol = RiskMetricsCalculator.calculate_volatility(returns)
        # Manual calculation: stdev([0.01, 0.02, -0.01, 0.03, -0.02])
        expected = statistics.stdev(returns)
        assert abs(vol - expected) < 1e-6

    def test_volatility_empty_list(self):
        """Test volatility with empty returns."""
        returns = []
        vol = RiskMetricsCalculator.calculate_volatility(returns)
        assert vol == 0.0

    def test_volatility_single_value(self):
        """Test volatility with single return."""
        returns = [0.01]
        vol = RiskMetricsCalculator.calculate_volatility(returns)
        assert vol == 0.0

    def test_annualized_volatility(self, sample_returns_series):
        """Test annualized volatility conversion."""
        daily_returns = sample_returns_series['RELIANCE.NS']
        ann_vol = RiskMetricsCalculator.calculate_annualized_volatility(daily_returns)

        daily_vol = statistics.stdev(daily_returns)
        expected = daily_vol * math.sqrt(252)

        assert abs(ann_vol - expected) < 1e-6
        # Should be roughly 20-50% annually
        assert 0.1 < ann_vol < 1.0

    def test_high_volatility_asset(self):
        """Test volatility for high-volatility asset."""
        returns = [r * 2 for r in [0.01, 0.02, -0.01, 0.03, -0.02]]
        vol = RiskMetricsCalculator.calculate_volatility(returns)

        low_vol = RiskMetricsCalculator.calculate_volatility([0.01, 0.02, -0.01, 0.03, -0.02])
        assert vol > low_vol


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Value at Risk (VaR)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestValueAtRisk:
    """Test VaR calculations."""

    def test_var_historical_95(self):
        """Test historical VaR at 95% confidence."""
        returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.00, 0.01, 0.02, 0.03, 0.04]
        var = RiskMetricsCalculator.calculate_var_historical(returns, confidence=0.95)

        # Sorted: [-0.05, -0.04, -0.03, -0.02, -0.01, 0.00, 0.01, 0.02, 0.03, 0.04]
        # 5% index (worst 5%) = index 0
        assert var == -0.05

    def test_var_historical_99(self):
        """Test historical VaR at 99% confidence."""
        # 100 returns: worst 1% is at index 0
        returns = sorted([0.01, -0.02, 0.015, -0.03] + [0.01] * 96)
        var = RiskMetricsCalculator.calculate_var_historical(returns, confidence=0.99)

        assert var <= returns[1]  # Should be in worst 1%

    def test_var_parametric_positive_return(self):
        """Test parametric VaR with positive expected return."""
        mean_return = 0.05  # 5% expected annual return
        volatility = 0.20   # 20% annual volatility
        portfolio_value = 100000.0

        var = RiskMetricsCalculator.calculate_var_parametric(
            mean_return, volatility, confidence=0.95, portfolio_value=portfolio_value
        )

        # VaR should be negative (loss scenario)
        assert var < 0
        assert var < portfolio_value * mean_return  # Loss can exceed expected return

    def test_var_parametric_vs_historical(self, sample_returns_series):
        """Compare parametric and historical VaR."""
        returns = sample_returns_series['RELIANCE.NS']

        mean_ret = statistics.mean(returns)
        vol = statistics.stdev(returns)

        var_param = RiskMetricsCalculator.calculate_var_parametric(mean_ret, vol, 0.95, 100000)
        var_hist = RiskMetricsCalculator.calculate_var_historical(returns, 0.95)

        # Should be in same ballpark
        assert abs(var_param - var_hist * 100000) < 100000

    def test_var_zero_volatility(self):
        """Test VaR with zero volatility."""
        var = RiskMetricsCalculator.calculate_var_parametric(0.01, 0.0, 0.95, 100000)
        # Should just be mean - 0 = mean
        assert abs(var - 1000.0) < 1.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Correlation & Covariance
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestCorrelation:
    """Test correlation and covariance calculations."""

    def test_correlation_perfect_positive(self):
        """Test perfect positive correlation."""
        returns_a = [0.01, 0.02, 0.03, 0.04, 0.05]
        returns_b = [0.02, 0.04, 0.06, 0.08, 0.10]  # 2x returns_a

        corr = RiskMetricsCalculator.calculate_correlation(returns_a, returns_b)
        assert abs(corr - 1.0) < 1e-6

    def test_correlation_perfect_negative(self):
        """Test perfect negative correlation."""
        returns_a = [0.01, 0.02, 0.03, 0.04, 0.05]
        returns_b = [-0.01, -0.02, -0.03, -0.04, -0.05]

        corr = RiskMetricsCalculator.calculate_correlation(returns_a, returns_b)
        assert abs(corr - (-1.0)) < 1e-6

    def test_correlation_no_correlation(self):
        """Test zero correlation."""
        returns_a = [0.01, -0.01, 0.02, -0.02, 0.01]
        returns_b = [-0.02, 0.01, 0.01, 0.02, -0.01]

        corr = RiskMetricsCalculator.calculate_correlation(returns_a, returns_b)
        # Should be close to 0
        assert abs(corr) < 0.5

    def test_correlation_sample_portfolio(self, sample_returns_series):
        """Test correlation between real portfolio stocks."""
        returns_reliance = sample_returns_series['RELIANCE.NS']
        returns_hdfc = sample_returns_series['HDFCBANK.NS']

        corr = RiskMetricsCalculator.calculate_correlation(returns_reliance, returns_hdfc)

        # Should be between -1 and 1
        assert -1.0 <= corr <= 1.0
        # Indian banks typically correlated with each other
        assert corr > 0

    def test_covariance_calculation(self):
        """Test covariance calculation."""
        returns_a = [0.01, 0.02, 0.03]
        returns_b = [0.02, 0.04, 0.06]

        cov = RiskMetricsCalculator.calculate_covariance(returns_a, returns_b)
        # Should be positive
        assert cov > 0

    def test_correlation_empty_series(self):
        """Test correlation with empty series."""
        corr = RiskMetricsCalculator.calculate_correlation([], [])
        assert corr == 0.0

    def test_correlation_mismatched_lengths(self):
        """Test correlation with mismatched series lengths."""
        corr = RiskMetricsCalculator.calculate_correlation([0.01, 0.02], [0.01, 0.02, 0.03])
        assert corr == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Beta
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestBeta:
    """Test beta calculations."""

    def test_beta_market_tracking(self):
        """Test beta when stock moves with market."""
        market_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        asset_returns = [0.01, 0.02, -0.01, 0.03, -0.02]  # Same as market

        beta = RiskMetricsCalculator.calculate_beta(asset_returns, market_returns)
        assert abs(beta - 1.0) < 0.01

    def test_beta_twice_market_volatility(self):
        """Test beta for asset with 2x market volatility."""
        market_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        asset_returns = [r * 2 for r in market_returns]  # 2x market moves

        beta = RiskMetricsCalculator.calculate_beta(asset_returns, market_returns)
        assert abs(beta - 2.0) < 0.01

    def test_beta_inverse_market(self):
        """Test beta for asset moving opposite to market."""
        market_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        asset_returns = [-r for r in market_returns]

        beta = RiskMetricsCalculator.calculate_beta(asset_returns, market_returns)
        assert abs(beta - (-1.0)) < 0.01

    def test_beta_zero_market_variance(self):
        """Test beta when market has no variance."""
        market_returns = [0.01, 0.01, 0.01]
        asset_returns = [0.02, 0.02, 0.02]

        beta = RiskMetricsCalculator.calculate_beta(asset_returns, market_returns)
        assert beta == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Sharpe Ratio
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestSharpeRatio:
    """Test Sharpe ratio calculations."""

    def test_sharpe_ratio_positive_excess_return(self):
        """Test Sharpe ratio with positive excess return."""
        portfolio_return = 0.15  # 15%
        portfolio_volatility = 0.10  # 10%
        risk_free_rate = 0.05  # 5%

        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(
            portfolio_return, portfolio_volatility, risk_free_rate
        )

        expected = (0.15 - 0.05) / 0.10  # = 1.0
        assert abs(sharpe - expected) < 1e-6

    def test_sharpe_ratio_negative_excess_return(self):
        """Test Sharpe ratio when return is below risk-free rate."""
        portfolio_return = 0.02
        portfolio_volatility = 0.10
        risk_free_rate = 0.05

        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(
            portfolio_return, portfolio_volatility, risk_free_rate
        )

        assert sharpe < 0  # Negative Sharpe

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio with zero volatility."""
        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(0.10, 0.0, 0.05)
        assert sharpe == 0.0

    def test_sharpe_ratio_comparison(self):
        """Test Sharpe ratio for comparing portfolios."""
        portfolio_a_return = 0.12
        portfolio_a_vol = 0.08

        portfolio_b_return = 0.14
        portfolio_b_vol = 0.12

        sharpe_a = RiskMetricsCalculator.calculate_sharpe_ratio(
            portfolio_a_return, portfolio_a_vol
        )
        sharpe_b = RiskMetricsCalculator.calculate_sharpe_ratio(
            portfolio_b_return, portfolio_b_vol
        )

        # A has better risk-adjusted return
        assert sharpe_a > sharpe_b


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Maximum Drawdown
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestMaximumDrawdown:
    """Test maximum drawdown calculations."""

    def test_max_drawdown_no_loss(self):
        """Test max drawdown when only positive returns."""
        returns = [0.01, 0.02, 0.03, 0.02, 0.01]
        dd = RiskMetricsCalculator.calculate_max_drawdown(returns)
        assert dd == 0.0

    def test_max_drawdown_single_drop(self):
        """Test max drawdown after single drop."""
        returns = [0.10, -0.10]  # Up 10%, down 10%
        dd = RiskMetricsCalculator.calculate_max_drawdown(returns)

        # Peak is 1.10, trough is 1.10 * 0.90 = 0.99
        # DD = (1.10 - 0.99) / 1.10 ≈ 0.0909
        expected = (1.10 - 0.99) / 1.10
        assert abs(dd - expected) < 0.001

    def test_max_drawdown_recovery(self):
        """Test max drawdown with recovery."""
        returns = [0.10, -0.20, 0.15]  # Up 10%, down 20%, up 15%
        dd = RiskMetricsCalculator.calculate_max_drawdown(returns)

        # Peak 1.10, drops to 1.10 * 0.80 = 0.88
        # Max DD = (1.10 - 0.88) / 1.10 ≈ 0.20
        expected = (1.10 - 0.88) / 1.10
        assert abs(dd - expected) < 0.001

    def test_max_drawdown_all_losses(self):
        """Test max drawdown when all negative returns."""
        returns = [-0.05, -0.05, -0.05]
        dd = RiskMetricsCalculator.calculate_max_drawdown(returns)

        # 1 → 0.95 → 0.9025 → 0.857375
        # DD = (1 - 0.857375) / 1 ≈ 0.1426
        expected = 1 - (0.95 ** 3)
        assert abs(dd - expected) < 0.001


# ──────────────────────────────────────────────────────────────────────────────
# Integration Tests: Risk Metrics
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestRiskMetricsIntegration:
    """Test combinations of risk metrics."""

    def test_portfolio_risk_profile(self, sample_returns_series):
        """Test complete portfolio risk profile."""
        returns = sample_returns_series['RELIANCE.NS']

        vol = RiskMetricsCalculator.calculate_volatility(returns)
        ann_vol = RiskMetricsCalculator.calculate_annualized_volatility(returns)
        var_95 = RiskMetricsCalculator.calculate_var_historical(returns, 0.95)
        var_99 = RiskMetricsCalculator.calculate_var_historical(returns, 0.99)
        sharpe = RiskMetricsCalculator.calculate_sharpe_ratio(0.10, ann_vol)

        # Validate relationships
        assert ann_vol == vol * math.sqrt(252)
        assert var_95 > var_99  # 95% VaR less severe than 99%
        assert var_95 < 0 and var_99 < 0  # Both should be negative (losses)

    def test_diversification_benefit(self, sample_returns_series):
        """Test that diversification reduces portfolio risk."""
        returns_a = sample_returns_series['RELIANCE.NS']
        returns_b = sample_returns_series['HDFCBANK.NS']

        vol_a = RiskMetricsCalculator.calculate_volatility(returns_a)
        vol_b = RiskMetricsCalculator.calculate_volatility(returns_b)

        # Combined volatility (50/50 weight)
        combined_returns = [(a + b) / 2 for a, b in zip(returns_a, returns_b)]
        vol_combined = RiskMetricsCalculator.calculate_volatility(combined_returns)

        corr = RiskMetricsCalculator.calculate_correlation(returns_a, returns_b)

        # With positive correlation, combined vol should be less than average
        if corr < 1.0:
            assert vol_combined < (vol_a + vol_b) / 2
