from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from backend.app.services.pa_calculator import DailyPAFactsCalculator


def _bar(index: int, close: float) -> SimpleNamespace:
    ts = datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=index)
    return SimpleNamespace(
        symbol_id="SPY",
        timeframe="1d",
        ts=ts,
        open=close - 1,
        high=close + 0.2,
        low=close - 2,
        close=close,
        volume=1_000_000 + (index * 1_000),
    )


def test_daily_pa_facts_calculator_adds_trend_and_range_facts() -> None:
    bars = [_bar(index, 100 + index) for index in range(280)]

    facts = DailyPAFactsCalculator.calculate(bars)
    latest = facts[-1].facts

    assert latest["above_sma_20"] is True
    assert latest["above_sma_50"] is True
    assert latest["above_sma_200"] is True
    assert latest["sma_20_slope_pct"] > 0
    assert latest["new_52w_high"] is True
    assert latest["close_near_high"] is True
    assert latest["return_3m"] > 0
    assert latest["return_12m"] > 0
    assert latest["relative_volume"] > 1
    assert latest["atr_14"] > 0
    assert latest["atr_pct"] > 0
    assert 0 <= latest["vol_rank"] <= 1
    assert facts[120].facts["vol_rank"] is None
