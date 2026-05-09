from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CalculatedPAFact:
    symbol_id: str
    timeframe: str
    ts: datetime
    facts: dict[str, Any]


class DailyPAFactsCalculator:
    @staticmethod
    def calculate(bars: Sequence[object]) -> list[CalculatedPAFact]:
        ordered_bars = sorted(bars, key=lambda bar: bar.ts)
        closes = [_as_float(bar.close) for bar in ordered_bars]
        highs = [_as_float(bar.high) for bar in ordered_bars]
        lows = [_as_float(bar.low) for bar in ordered_bars]
        volumes = [_as_float(bar.volume) for bar in ordered_bars]
        range_pcts = [
            _safe_div(_as_float(bar.high) - _as_float(bar.low), _as_float(bar.close))
            if _has_ohlc(bar)
            else None
            for bar in ordered_bars
        ]

        calculated: list[CalculatedPAFact] = []
        for index, bar in enumerate(ordered_bars):
            if not _has_ohlc(bar):
                continue

            close = _as_float(bar.close)
            high = _as_float(bar.high)
            low = _as_float(bar.low)
            volume = _as_float(bar.volume)
            sma_20 = _average(closes, index, 20)
            sma_50 = _average(closes, index, 50)
            sma_200 = _average(closes, index, 200)
            volume_sma_20 = _average(volumes, index, 20)
            range_pct_5d_avg = _average(range_pcts, index, 5)
            range_pct_20d_avg = _average(range_pcts, index, 20)
            high_52w = _rolling_max(highs, index, 252)
            low_52w = _rolling_min(lows, index, 252)
            high_60d = _rolling_max(highs, index, 60)
            low_60d = _rolling_min(lows, index, 60)
            previous_high_252 = _rolling_max(highs, index - 1, 252) if index > 0 else None
            previous_low_252 = _rolling_min(lows, index - 1, 252) if index > 0 else None

            facts = {
                "open": _rounded(_as_float(bar.open)),
                "high": _rounded(high),
                "low": _rounded(low),
                "close": _rounded(close),
                "volume": _rounded(volume),
                "range": _rounded(high - low),
                "range_pct": _rounded(_safe_div(high - low, close)),
                "close_position_in_range": _rounded(_safe_div(close - low, high - low)),
                "close_near_high": _safe_div(close - low, high - low) is not None
                and _safe_div(close - low, high - low) >= 0.8,
                "close_near_low": _safe_div(close - low, high - low) is not None
                and _safe_div(close - low, high - low) <= 0.2,
                "sma_20": _rounded(sma_20),
                "sma_50": _rounded(sma_50),
                "sma_200": _rounded(sma_200),
                "distance_to_sma_20_pct": _rounded(_pct_diff(close, sma_20)),
                "distance_to_sma_50_pct": _rounded(_pct_diff(close, sma_50)),
                "distance_to_sma_200_pct": _rounded(_pct_diff(close, sma_200)),
                "above_sma_20": _above(close, sma_20),
                "above_sma_50": _above(close, sma_50),
                "above_sma_200": _above(close, sma_200),
                "sma_20_slope_pct": _rounded(_sma_slope(closes, index, 20, 5)),
                "high_52w": _rounded(high_52w),
                "low_52w": _rounded(low_52w),
                "new_52w_high": previous_high_252 is not None and high >= previous_high_252,
                "new_52w_low": previous_low_252 is not None and low <= previous_low_252,
                "pct_from_52w_high": _rounded(_pct_diff(close, high_52w)),
                "pct_above_52w_low": _rounded(_pct_diff(close, low_52w)),
                "volume_sma_20": _rounded(volume_sma_20),
                "relative_volume": _rounded(_safe_div(volume, volume_sma_20)),
                "return_1d": _rounded(_return(closes, index, 1)),
                "return_1m": _rounded(_return(closes, index, 21)),
                "return_3m": _rounded(_return(closes, index, 63)),
                "return_6m": _rounded(_return(closes, index, 126)),
                "return_12m": _rounded(_return(closes, index, 252)),
                "high_60d": _rounded(high_60d),
                "low_60d": _rounded(low_60d),
                "base_depth_60d": _rounded(_safe_div(high_60d - low_60d, high_60d))
                if high_60d is not None and low_60d is not None
                else None,
                "range_pct_5d_avg": _rounded(range_pct_5d_avg),
                "range_pct_20d_avg": _rounded(range_pct_20d_avg),
                "volatility_contraction": range_pct_5d_avg is not None
                and range_pct_20d_avg is not None
                and range_pct_5d_avg < range_pct_20d_avg,
            }
            calculated.append(
                CalculatedPAFact(
                    symbol_id=bar.symbol_id,
                    timeframe=bar.timeframe,
                    ts=bar.ts,
                    facts=facts,
                )
            )
        return calculated


def _has_ohlc(bar: object) -> bool:
    return (
        _as_float(bar.open) is not None
        and _as_float(bar.high) is not None
        and _as_float(bar.low) is not None
        and _as_float(bar.close) is not None
    )


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def _safe_div(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def _average(values: Sequence[float | None], index: int, window: int) -> float | None:
    if index < window - 1:
        return None
    sample = values[index - window + 1 : index + 1]
    if any(value is None for value in sample):
        return None
    return sum(value for value in sample if value is not None) / window


def _rolling_max(values: Sequence[float | None], index: int, window: int) -> float | None:
    if index < 0:
        return None
    sample = [value for value in values[max(0, index - window + 1) : index + 1] if value is not None]
    return max(sample) if sample else None


def _rolling_min(values: Sequence[float | None], index: int, window: int) -> float | None:
    if index < 0:
        return None
    sample = [value for value in values[max(0, index - window + 1) : index + 1] if value is not None]
    return min(sample) if sample else None


def _pct_diff(value: float | None, reference: float | None) -> float | None:
    if value is None or reference in (None, 0):
        return None
    return (value / reference) - 1


def _above(value: float | None, reference: float | None) -> bool | None:
    if value is None or reference is None:
        return None
    return value > reference


def _sma_slope(
    values: Sequence[float | None],
    index: int,
    window: int,
    lookback: int,
) -> float | None:
    current = _average(values, index, window)
    previous = _average(values, index - lookback, window) if index >= lookback else None
    return _pct_diff(current, previous)


def _return(values: Sequence[float | None], index: int, lookback: int) -> float | None:
    if index < lookback:
        return None
    return _pct_diff(values[index], values[index - lookback])
