TOP_100 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "UNH", "HD", "BAC", "XOM", "DIS", "ADBE",
    "CRM", "NFLX", "PFE", "KO", "PEP", "T", "CSCO", "INTC", "ABT", "CVX",
    "MRK", "VZ", "ORCL", "NKE", "MCD", "DHR", "ACN", "COST", "AVGO", "WFC",
    "TXN", "QCOM", "LIN", "AMD", "HON", "LOW", "UPS", "IBM", "PM", "INTU",
    "CAT", "AMAT", "GS", "RTX", "SBUX", "BLK", "PLD", "SPGI", "MDT", "NOW",
    "DE", "ISRG", "ADI", "BKNG", "GILD", "LRCX", "ZTS", "MO", "MMC", "AXP",
    "SYK", "CI", "TMO", "ELV", "DUK", "SO", "SCHW", "APD", "CB", "EOG",
    "BDX", "PGR", "USB", "CSX", "ETN", "CL", "NSC", "HUM", "ITW", "AON",
    "GM", "F", "RIVN", "SNOW", "UBER", "LYFT", "SHOP", "SQ", "PYPL", "COIN",
]

PRIORITY = [
    "AAPL", "TSLA", "NVDA", "MSFT", "GOOGL",
    "AMZN", "META", "AMD", "NFLX", "SPY",
]

REMAINING_TOP_100 = [ticker for ticker in TOP_100 if ticker not in PRIORITY]
