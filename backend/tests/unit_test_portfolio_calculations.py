"""
Unit tests for portfolio calculations.

Test cases:
- Portfolio value calculations
- Cost basis and P&L
- Allocation percentages
- Return calculations (absolute, percentage)
- Portfolio rebalancing logic
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta
from decimal import Decimal


class PortfolioCalculator:
    """Utility class for portfolio calculations (to be mocked/imported from app)."""

    @staticmethod
    def calculate_cost_basis(quantity: float, purchase_price: float) -> float:
        """Calculate total cost basis."""
        return quantity * purchase_price

    @staticmethod
    def calculate_current_value(quantity: float, current_price: float) -> float:
        """Calculate current market value."""
        return quantity * current_price

    @staticmethod
    def calculate_unrealised_pnl(current_value: float, cost_basis: float) -> float:
        """Calculate unrealised P&L (absolute)."""
        return current_value - cost_basis

    @staticmethod
    def calculate_pnl_percentage(unrealised_pnl: float, cost_basis: float) -> float:
        """Calculate P&L as percentage."""
        if cost_basis == 0:
            return 0.0
        return (unrealised_pnl / cost_basis) * 100

    @staticmethod
    def calculate_allocation(value: float, portfolio_value: float) -> float:
        """Calculate allocation percentage."""
        if portfolio_value == 0:
            return 0.0
        return (value / portfolio_value) * 100

    @staticmethod
    def calculate_portfolio_value(holdings: list[dict]) -> float:
        """Calculate total portfolio value."""
        return sum(h['current_value'] for h in holdings)

    @staticmethod
    def calculate_portfolio_cost_basis(holdings: list[dict]) -> float:
        """Calculate total cost basis."""
        return sum(h['cost_basis'] for h in holdings)

    @staticmethod
    def calculate_portfolio_pnl(holdings: list[dict]) -> float:
        """Calculate total portfolio P&L."""
        return sum(h['unrealised_pnl'] for h in holdings)


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Individual Holdings
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestHoldingCalculations:
    """Test calculations for single holdings."""

    def test_cost_basis_calculation(self):
        """Test cost basis = quantity × purchase_price."""
        assert PortfolioCalculator.calculate_cost_basis(100, 2500.0) == 250000.0
        assert PortfolioCalculator.calculate_cost_basis(50, 1500.0) == 75000.0
        assert PortfolioCalculator.calculate_cost_basis(0, 2500.0) == 0.0

    def test_current_value_calculation(self):
        """Test current_value = quantity × current_price."""
        assert PortfolioCalculator.calculate_current_value(100, 2875.5) == 287550.0
        assert PortfolioCalculator.calculate_current_value(50, 1680.5) == 84025.0

    def test_unrealised_pnl_calculation(self):
        """Test unrealised_pnl = current_value - cost_basis."""
        # Reliance: bought 100 @ 2500, now 2875.5
        cost_basis = 250000.0
        current_value = 287550.0
        pnl = PortfolioCalculator.calculate_unrealised_pnl(current_value, cost_basis)
        assert pnl == 37550.0

        # HDFC: bought 50 @ 1500, now 1680.5
        cost_basis = 75000.0
        current_value = 84025.0
        pnl = PortfolioCalculator.calculate_unrealised_pnl(current_value, cost_basis)
        assert pnl == 9025.0

    def test_pnl_percentage_calculation(self):
        """Test P&L percentage = (unrealised_pnl / cost_basis) × 100."""
        # Reliance: 37550 profit on 250000 cost = 15.02%
        pnl_pct = PortfolioCalculator.calculate_pnl_percentage(37550.0, 250000.0)
        assert abs(pnl_pct - 15.02) < 0.01

        # HDFC: 9025 profit on 75000 cost = 12.03%
        pnl_pct = PortfolioCalculator.calculate_pnl_percentage(9025.0, 75000.0)
        assert abs(pnl_pct - 12.03) < 0.01

        # Loss scenario
        pnl_pct = PortfolioCalculator.calculate_pnl_percentage(-5000.0, 100000.0)
        assert pnl_pct == -5.0

    def test_pnl_percentage_zero_cost_basis(self):
        """Test P&L percentage with zero cost basis."""
        pnl_pct = PortfolioCalculator.calculate_pnl_percentage(100.0, 0.0)
        assert pnl_pct == 0.0

    def test_allocation_calculation(self):
        """Test allocation = (holding_value / portfolio_value) × 100."""
        # Reliance worth 287550 in portfolio worth 625000
        alloc = PortfolioCalculator.calculate_allocation(287550.0, 625000.0)
        assert abs(alloc - 46.01) < 0.01

    def test_allocation_zero_portfolio(self):
        """Test allocation with zero portfolio value."""
        alloc = PortfolioCalculator.calculate_allocation(100.0, 0.0)
        assert alloc == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Portfolio Level
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestPortfolioCalculations:
    """Test calculations for entire portfolio."""

    def test_portfolio_value_calculation(self, sample_portfolio_india, sample_quotes):
        """Test total portfolio value."""
        holdings = [
            {
                'yf_ticker': h.yf_ticker,
                'quantity': h.quantity,
                'current_price': sample_quotes[h.yf_ticker]['close'],
                'current_value': h.quantity * sample_quotes[h.yf_ticker]['close'],
            }
            for h in sample_portfolio_india
            if h.yf_ticker in sample_quotes
        ]
        portfolio_value = PortfolioCalculator.calculate_portfolio_value(holdings)
        assert portfolio_value > 0
        # Verify it's approximately 625000 (sum of all current values)
        assert 600000 < portfolio_value < 650000

    def test_portfolio_cost_basis(self, sample_portfolio_india):
        """Test total cost basis."""
        holdings = [
            {
                'quantity': h.quantity,
                'purchase_price': h.purchase_price,
                'cost_basis': h.quantity * h.purchase_price,
            }
            for h in sample_portfolio_india
        ]
        cost_basis = PortfolioCalculator.calculate_portfolio_cost_basis(holdings)
        # 100*2500 + 50*1500 + 200*1350 + 75*3200 + 30*2000
        # = 250000 + 75000 + 270000 + 240000 + 60000 = 895000
        assert cost_basis == 895000.0

    def test_portfolio_pnl(self):
        """Test total portfolio P&L."""
        holdings = [
            {'unrealised_pnl': 37550.0},
            {'unrealised_pnl': 9025.0},
            {'unrealised_pnl': -5000.0},
        ]
        total_pnl = PortfolioCalculator.calculate_portfolio_pnl(holdings)
        assert total_pnl == 41575.0

    def test_portfolio_pnl_negative(self):
        """Test total portfolio P&L (all losses)."""
        holdings = [
            {'unrealised_pnl': -10000.0},
            {'unrealised_pnl': -5000.0},
        ]
        total_pnl = PortfolioCalculator.calculate_portfolio_pnl(holdings)
        assert total_pnl == -15000.0

    def test_empty_portfolio(self):
        """Test calculations on empty portfolio."""
        holdings = []
        assert PortfolioCalculator.calculate_portfolio_value(holdings) == 0.0
        assert PortfolioCalculator.calculate_portfolio_cost_basis(holdings) == 0.0
        assert PortfolioCalculator.calculate_portfolio_pnl(holdings) == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Return Calculations
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestReturnCalculations:
    """Test various return calculations."""

    @staticmethod
    def calculate_holding_return(current_price: float, purchase_price: float) -> float:
        """Calculate return per unit."""
        return current_price - purchase_price

    @staticmethod
    def calculate_time_weighted_return(start_value: float, end_value: float, days: int) -> float:
        """Calculate annualized return."""
        if start_value == 0:
            return 0.0
        total_return = (end_value - start_value) / start_value
        years = days / 365.0
        if years == 0:
            return 0.0
        return (total_return / years) * 100

    def test_holding_return(self):
        """Test per-unit return."""
        ret = self.calculate_holding_return(2875.5, 2500.0)
        assert ret == 375.5

        ret = self.calculate_holding_return(1680.5, 1500.0)
        assert ret == 180.5

    def test_time_weighted_return_1year(self):
        """Test annualized return over 1 year."""
        start_value = 250000.0
        end_value = 287550.0
        ret = self.calculate_time_weighted_return(start_value, end_value, 365)
        assert abs(ret - 15.02) < 0.1

    def test_time_weighted_return_6months(self):
        """Test annualized return over 6 months."""
        start_value = 250000.0
        end_value = 275000.0
        ret = self.calculate_time_weighted_return(start_value, end_value, 182)
        # (25000 / 250000) / 0.5 * 100 = 20%
        assert abs(ret - 20.0) < 0.1

    def test_time_weighted_return_zero_start(self):
        """Test return with zero starting value."""
        ret = self.calculate_time_weighted_return(0.0, 100.0, 365)
        assert ret == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Rebalancing Logic
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestRebalancingLogic:
    """Test portfolio rebalancing calculations."""

    @staticmethod
    def detect_drift(current_allocation: dict, target_allocation: dict, threshold: float) -> list[str]:
        """Detect positions that have drifted beyond threshold."""
        drifts = []
        for ticker, target in target_allocation.items():
            current = current_allocation.get(ticker, 0.0)
            deviation = abs(current - target)
            if deviation > threshold:
                drifts.append(ticker)
        return drifts

    @staticmethod
    def calculate_rebalance_action(
        current_value: float,
        target_allocation: float,
        portfolio_value: float,
    ) -> float:
        """Calculate shares to buy/sell for rebalancing."""
        target_value = portfolio_value * target_allocation
        return target_value - current_value

    def test_detect_drift_within_threshold(self):
        """Test detection when drift is within threshold."""
        current = {'RELIANCE': 0.45, 'HDFC': 0.35, 'INFY': 0.20}
        target = {'RELIANCE': 0.40, 'HDFC': 0.35, 'INFY': 0.25}
        threshold = 0.10  # 10% tolerance

        drifts = self.detect_drift(current, target, threshold)
        assert len(drifts) == 0  # No drifts within 10%

    def test_detect_drift_exceeds_threshold(self):
        """Test detection when drift exceeds threshold."""
        current = {'RELIANCE': 0.50, 'HDFC': 0.30, 'INFY': 0.20}
        target = {'RELIANCE': 0.40, 'HDFC': 0.35, 'INFY': 0.25}
        threshold = 0.05  # 5% tolerance

        drifts = self.detect_drift(current, target, threshold)
        assert 'RELIANCE' in drifts
        assert 'HDFC' in drifts
        assert 'INFY' in drifts

    def test_calculate_rebalance_action_buy(self):
        """Test rebalancing when need to buy."""
        current_value = 250000.0  # RELIANCE currently worth 250k
        target_allocation = 0.40
        portfolio_value = 625000.0

        action = self.calculate_rebalance_action(current_value, target_allocation, portfolio_value)
        # Target should be 625000 * 0.40 = 250000
        # Current is 250000, so action = 0
        assert action == 0.0

    def test_calculate_rebalance_action_sell(self):
        """Test rebalancing when need to sell."""
        current_value = 300000.0  # RELIANCE now worth more
        target_allocation = 0.40
        portfolio_value = 625000.0

        action = self.calculate_rebalance_action(current_value, target_allocation, portfolio_value)
        # Target should be 625000 * 0.40 = 250000
        # Current is 300000, so need to sell 50000
        assert action == -50000.0

    def test_calculate_rebalance_action_buy_more(self):
        """Test rebalancing when need to buy more."""
        current_value = 200000.0  # RELIANCE worth less
        target_allocation = 0.40
        portfolio_value = 625000.0

        action = self.calculate_rebalance_action(current_value, target_allocation, portfolio_value)
        # Target should be 625000 * 0.40 = 250000
        # Current is 200000, so need to buy 50000
        assert action == 50000.0


# ──────────────────────────────────────────────────────────────────────────────
# Unit Tests: Edge Cases
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases in portfolio calculations."""

    def test_very_large_numbers(self):
        """Test with very large portfolio values."""
        quantity = 1_000_000
        price = 1000.0
        current_value = PortfolioCalculator.calculate_current_value(quantity, price)
        assert current_value == 1_000_000_000.0

    def test_very_small_numbers(self):
        """Test with fractional shares."""
        quantity = 0.5
        price = 2875.5
        current_value = PortfolioCalculator.calculate_current_value(quantity, price)
        assert abs(current_value - 1437.75) < 0.01

    def test_negative_pnl(self):
        """Test handling negative P&L."""
        cost_basis = 100000.0
        current_value = 95000.0
        pnl = PortfolioCalculator.calculate_unrealised_pnl(current_value, cost_basis)
        assert pnl == -5000.0

    def test_floating_point_precision(self):
        """Test floating point precision in calculations."""
        # Sum of percentages should be close to 100%
        allocations = [33.333, 33.333, 33.334]
        total = sum(allocations)
        assert abs(total - 100.0) < 0.001

    def test_portfolio_with_single_holding(self):
        """Test portfolio with single holding."""
        holdings = [
            {
                'yf_ticker': 'RELIANCE.NS',
                'quantity': 100,
                'purchase_price': 2500.0,
                'current_price': 2875.5,
                'cost_basis': 250000.0,
                'current_value': 287550.0,
                'unrealised_pnl': 37550.0,
            }
        ]
        portfolio_value = PortfolioCalculator.calculate_portfolio_value(holdings)
        cost_basis = PortfolioCalculator.calculate_portfolio_cost_basis(holdings)
        pnl = PortfolioCalculator.calculate_portfolio_pnl(holdings)

        assert portfolio_value == 287550.0
        assert cost_basis == 250000.0
        assert pnl == 37550.0
