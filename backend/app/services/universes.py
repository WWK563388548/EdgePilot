US_ETF_UNIVERSE = [
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "SMH",
    "SOXX",
    "XLK",
    "XLF",
    "XLE",
    "XLI",
    "XLY",
    "XLP",
    "XLU",
    "XLV",
    "TLT",
    "HYG",
    "LQD",
    "GLD",
    "SLV",
    "USO",
]


def default_symbols_when_omitted(symbols: list[str] | None) -> list[str]:
    if symbols is None:
        return list(US_ETF_UNIVERSE)
    return symbols
