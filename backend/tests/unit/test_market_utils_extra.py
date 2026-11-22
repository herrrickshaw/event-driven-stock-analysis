"""Remaining db/market_utils.py branches: CurrencyRate, empty / column-less
quality metrics, MarketStatistics.summary."""

from datetime import date

import pandas as pd
import pytest

from db.market_utils import CurrencyRate, DataQualityValidator, MarketStatistics


@pytest.mark.unit
class TestCurrencyRate:
    def test_convert_multiplies_by_rate(self):
        r = CurrencyRate("INR", "USD", 0.012, date(2024, 1, 1))
        assert r.convert(1000) == pytest.approx(12.0)
        assert r.convert(0) == 0
        assert r.convert(-50) == pytest.approx(-0.6)


@pytest.mark.unit
class TestQualityMetricsEdges:
    def test_empty_frame_returns_all_zero_metrics(self):
        m = DataQualityValidator.compute_metrics(pd.DataFrame({"Close": [], "Volume": []}))
        assert m == type(m)(0, 0, 0, 0, 0, 0, 0, 0)

    def test_custom_column_names_are_used(self):
        df = pd.DataFrame({"px": [1.0, 1.0, 100.0], "vol": [1.0, 1.0, 1.0]})
        m = DataQualityValidator.compute_metrics(df, price_col="px", volume_col="vol")
        assert m.total_records == 3 and m.outlier_records == 1

    def test_price_spike_threshold_is_strictly_above_500_percent(self):
        # +500% exactly (1 -> 6) is not an outlier; +600% is
        base = {"Volume": [10.0, 10.0]}
        at = DataQualityValidator.compute_metrics(pd.DataFrame({"Close": [1.0, 6.0], **base}))
        over = DataQualityValidator.compute_metrics(pd.DataFrame({"Close": [1.0, 7.0], **base}))
        assert at.outlier_records == 0 and over.outlier_records == 1

    def test_volume_spike_threshold_is_strictly_above_1000_percent(self):
        base = {"Close": [1.0, 1.0]}
        at = DataQualityValidator.compute_metrics(pd.DataFrame({**base, "Volume": [1.0, 11.0]}))
        over = DataQualityValidator.compute_metrics(pd.DataFrame({**base, "Volume": [1.0, 12.0]}))
        assert at.outlier_records == 0 and over.outlier_records == 1


@pytest.mark.unit
def test_market_statistics_summary_formats_every_field():
    s = MarketStatistics("usa", 7400, 1234567, 166.8, 5.04, (0.5, 3500.0), (0, 9000000)).summary()
    assert "Market: usa" in s
    assert "Total stocks: 7,400" in s and "Total records: 1,234,567" in s
    assert "Avg records/stock: 167" in s and "Date range: 5.0 years" in s
    assert "Price range: $0.50 - $3500.00" in s and "Volume range: 0 - 9,000,000" in s
