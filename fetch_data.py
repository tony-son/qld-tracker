#!/usr/bin/env python3
"""Fetches QLD/VIX market data from Yahoo Finance and writes compact data.json.
Runs inside GitHub Actions (see .github/workflows/update-data.yml)."""
import json
import time
import datetime
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def get(sym, rng, interval, retries=3):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{urllib.parse.quote(sym)}?range={rng}&interval={interval}"
    )
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.load(r)
            res = j["chart"]["result"][0]
            ts = res.get("timestamp", [])
            cl = res["indicators"]["quote"][0]["close"]
            dates, closes = [], []
            for t, c in zip(ts, cl):
                if c is not None:
                    dates.append(datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"))
                    closes.append(round(c, 4))
            if len(dates) < 2:
                raise ValueError(f"too few rows for {sym}")
            return {
                "dates": dates,
                "closes": closes,
                "price": res["meta"].get("regularMarketPrice"),
            }
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"FAILED {sym}: {last_err}")


def optional(sym, rng, interval):
    try:
        return get(sym, rng, interval)
    except SystemExit:
        return None


out = {"updated": datetime.datetime.utcnow().isoformat() + "Z"}
out["qldW"] = get("QLD", "10y", "1wk"); time.sleep(1)
out["vixW"] = get("^VIX", "10y", "1wk"); time.sleep(1)
out["qldD"] = get("QLD", "2y", "1d"); time.sleep(1)
out["vixD"] = get("^VIX", "2y", "1d"); time.sleep(1)
out["vix3m"] = optional("^VIX3M", "5d", "1d"); time.sleep(1)
out["vix9d"] = optional("^VIX9D", "5d", "1d"); time.sleep(1)
out["irx"] = optional("^IRX", "5d", "1d")

with open("data.json", "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"data.json written: {sum(len(v['dates']) for v in out.values() if isinstance(v, dict) and 'dates' in v)} rows")
