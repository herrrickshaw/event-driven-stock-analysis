"""Characterisation snapshot of the pure parts of the backend data/event layer.

`tests/golden/baseline.json` was captured from the ORIGINAL (pre-refactor)
code; `capture()` must keep reproducing it exactly. No network, no database.
"""
from __future__ import annotations

import asyncio
import importlib
import json
import os
from datetime import date
from pathlib import Path


def capture(workdir: Path) -> dict:
    """Run the fixed scenario and return JSON-able results (cwd is switched to workdir)."""
    import numpy as np
    import pandas as pd

    os.chdir(workdir)  # module import may drop a log file in cwd
    mu = importlib.import_module("db.market_utils")
    lh = importlib.import_module("db.load_historical_data")
    from events.event_bus import EventBus, MarketEvent
    from events.portfolio_monitor import PortfolioMonitor

    res = {}
    for m in ["india","usa","uk","japan","korea","europe","china","brazil","mars"]:
        hs = mu.MarketHolidayCalendar.get_holidays(m)
        res[f"hol_{m}"] = sorted(map(str, hs))
        res[f"hol2024_{m}"] = sorted(map(str, mu.MarketHolidayCalendar.get_holidays(m, 2024)))
        res[f"next_{m}"] = str(mu.MarketHolidayCalendar.next_trading_day(m, date(2024,12,24)))
        res[f"prev_{m}"] = str(mu.MarketHolidayCalendar.prev_trading_day(m, date(2025,1,2)))
        res[f"td_{m}"] = [mu.MarketHolidayCalendar.is_trading_day(m, date(2025,d1,d2)) for d1,d2 in [(1,1),(1,4),(1,6),(12,25)]]
    conv = []
    for a,f,t in [(1000,'INR','USD'),(100,'EUR','USD'),(5,'USD','EUR'),(5,'USD','XXX'),(3,'XXX','USD'),(7,'GBP','GBP'),(10,'INR','EUR')]:
        conv.append(mu.CurrencyConverter.convert_price(a,f,t))
    res["conv"] = conv
    res["norm"] = mu.CurrencyConverter.normalize_prices({'A':1000,'B':10,'C':2},{'A':'INR','B':'EUR'})
    rng = np.random.RandomState(0)
    n = 300
    close = 100 + rng.randn(n).cumsum()
    df = pd.DataFrame({'Open':close*0.99,'High':close*1.02,'Low':close*0.97,'Close':close,'Volume':rng.randint(1000,5000,n).astype(float),'Adj Close':close},
                      index=pd.date_range('2023-01-02', periods=n, freq='B'))
    df.loc[df.index[5],'Close'] = np.nan
    df.loc[df.index[9],'Volume'] = np.nan
    df = pd.concat([df, df.iloc[[20]]])
    m = mu.DataQualityValidator.compute_metrics(df)
    res["dq"] = {k:(float(v) if not isinstance(v,(int,float)) else v) for k,v in vars(m).items()}
    res["dq_score"] = float(m.quality_score)
    res["dq_ok"] = [bool(mu.DataQualityValidator.is_quality_acceptable(m)), bool(mu.DataQualityValidator.is_quality_acceptable(m, 50, 50, 50))]
    res["yf"] = [mu.MarketConfig.get_yfinance_ticker(t,mk) for t,mk in [('RELIANCE','india'),('AAPL','usa'),('7203','japan'),('X.DE','europe'),('X.NS','india'),('005930','korea'),('x','mars'),('600519','china')]]
    res["local"] = [mu.MarketConfig.get_local_ticker(t,mk) for t,mk in [('RELIANCE.NS','india'),('AAPL','usa'),('7203.T','japan'),('X.DE','europe')]]
    ms = mu.MarketStatistics('india',10,100,10.0,5.0,(1.0,2.0),(1,2))
    res["summary"] = ms.summary()
    # loader pure bits
    f = lh.HistoricalDataFetcher(None, 'india')
    clean = f.validate_ohlcv(df.dropna(subset=['Close']).copy(), 'T')
    res["clean_shape"] = None if clean is None else list(clean.shape)
    res["clean_cols"] = None if clean is None else list(clean.columns)
    res["clean_sum"] = None if clean is None else float(clean['Close'].sum())
    res["clean_short"] = f.validate_ohlcv(df.head(10).copy(), 'T') is None
    recs = f.convert_to_ohlcv_records(clean.head(5), 7)
    res["recs"] = [list(map(str, r.to_tuple())) for r in recs]
    no_adj = f.convert_to_ohlcv_records(clean.drop(columns=['Adj Close']).head(2), 7)
    res["recs_noadj"] = [list(map(str, r.to_tuple())) for r in no_adj]
    res["list_predef"] = {k: lh.StockListLoader.load_predefined(k) for k in ['india','usa','japan']}
    csv_path = workdir / "stocks.csv"
    csv_path.write_text("Ticker,Name\nAAA,Alpha\n,Blank\nbbb,\n")
    res["list_csv"] = lh.StockListLoader.load_from_csv(str(csv_path),"india")
    res["list_csv_missing"] = lh.StockListLoader.load_from_csv(str(workdir / "nope.csv"),"india")
    lp = lh.LoadProgress(market='india', total_stocks=10)
    res["eta_none"] = lp.get_eta()
    # bus
    from events.event_bus import EventBus, MarketEvent
    from events.portfolio_monitor import PortfolioMonitor
    async def bus_run():
        b = EventBus(max_history=3); seen=[]
        async def acb(e): seen.append(("a",e.type))
        b.subscribe("x", lambda e: seen.append(("s",e.type))); b.subscribe("*", acb); b.subscribe("y", acb)
        for t in "xyxz": await b.publish(MarketEvent(t,"T","india"))
        b.unsubscribe("x", acb)
        return seen, [e.type for e in b.history]
    res["bus"] = asyncio.run(bus_run())
    pm = PortfolioMonitor(); pm.add_tickers(["A","B"],"india"); pm.remove_ticker("A"); pm.remove_ticker("Z")
    res["mon"] = [pm.watched(), pm.is_monitoring("B"), pm.is_monitoring("A")]
    return json.loads(json.dumps(res, sort_keys=True, default=str))
