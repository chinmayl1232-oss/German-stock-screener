#
#German Market - Wave 2 Scanner (40W EMA)
#
#Scans DAX/MDAX/SDAX/TecDAX stocks for “second wave” setups close to 40W EMA.
#Outputs  data.json  for the iOS web app hosted on GitHub Pages.
#
#Auto-discovers tickers by scraping Wikipedia index pages (no API key needed).
#
#Usage:
#pip install yfinance pandas rich requests beautifulsoup4
#python scanner.py

#Outputs:
#data.json  — consumed by index.html web app

import sys, json, datetime, warnings
warnings.filterwarnings("ignore")

REQUIRED = {
"yfinance":       "yfinance",
"pandas":         "pandas",
"rich":           "rich",
"requests":       "requests",
"bs4":            "bs4",
}
missing = [pkg for pkg, imp in REQUIRED.items() if not **import**(imp, globals(), locals(), [], 0) or False]
try:
for pkg, imp in REQUIRED.items():
**import**(imp)
except ImportError as e:
print(f”\n❌  Missing package. Run:\n    pip install {’ ’.join(REQUIRED)}\n”)
sys.exit(1)

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

# ── config ────────────────────────────────────────────────────────────────────

EMA_WEEKS         = 40
MAX_DIST_PCT      = 15.0   # max % above 40W EMA
MIN_DIST_PCT      = 0.0    # must be above EMA
MIN_WAVE1_GAIN    = 30.0   # wave 1 must be ≥30% gain
MIN_PULLBACK_PCT  = 15.0   # pullback from W1 high must be ≥15%
VOLUME_DAYS       = 20
CHART_WEEKS       = 20     # weeks of history for sparkline

# ── sector map (ticker → sector) — fallback if Wikipedia doesn’t provide ──────

SECTOR_OVERRIDES = {
“SAP”: “Technology”,   “SIE”: “Industrials”,  “ALV”: “Financials”,
“MUV2”:“Financials”,   “DHL”: “Logistics”,    “BAS”: “Chemicals”,
“DBK”: “Financials”,   “EOAN”:“Utilities”,    “BMW”: “Automotive”,
“MBG”: “Automotive”,   “VOW3”:“Automotive”,   “ADS”: “Consumer”,
“HEN3”:“Consumer”,     “BAYN”:“Healthcare”,   “MRK”: “Healthcare”,
“FRE”: “Healthcare”,   “DTE”: “Telecom”,      “RWE”: “Utilities”,
“BEI”: “Consumer”,     “MTX”: “Industrials”,  “AIR”: “Industrials”,
“ENR”: “Energy”,       “ZAL”: “Consumer”,     “HNR1”:“Financials”,
“VNA”: “Real Estate”,
}

# ── Wikipedia index scraper ───────────────────────────────────────────────────

WIKI_URLS = {
“DAX”:    “https://en.wikipedia.org/wiki/DAX”,
“MDAX”:   “https://en.wikipedia.org/wiki/MDAX”,
“SDAX”:   “https://en.wikipedia.org/wiki/SDAX”,
“TecDAX”: “https://en.wikipedia.org/wiki/TecDAX”,
}

def scrape_tickers_from_wikipedia() -> dict[str, tuple[str,str]]:
“”“Returns {ticker_DE: (name, sector)}”””
tickers = {}
headers = {“User-Agent”: “Mozilla/5.0 (compatible; StockScanner/1.0)”}
for index_name, url in WIKI_URLS.items():
try:
resp = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, “html.parser”)
# find the constituents table
for table in soup.find_all(“table”, {“class”: “wikitable”}):
headers_row = [th.get_text(strip=True).lower() for th in table.find_all(“th”)]
# look for a column containing ‘ticker’ or ‘symbol’
ticker_col = next((i for i, h in enumerate(headers_row) if “ticker” in h or “symbol” in h), None)
name_col   = next((i for i, h in enumerate(headers_row) if “compan” in h or “name” in h), None)
sector_col = next((i for i, h in enumerate(headers_row) if “sector” in h or “industr” in h), None)
if ticker_col is None:
continue
for row in table.find_all(“tr”)[1:]:
cells = row.find_all([“td”,“th”])
if len(cells) <= ticker_col:
continue
raw = cells[ticker_col].get_text(strip=True)
# clean ticker
ticker = raw.split(”[”)[0].split(”(”)[0].strip().upper()
if not ticker or len(ticker) > 8:
continue
name   = cells[name_col].get_text(strip=True).split(”[”)[0] if name_col and len(cells) > name_col else ticker
sector = cells[sector_col].get_text(strip=True).split(”[”)[0] if sector_col and len(cells) > sector_col else “”
# override sector if we have a better mapping
sector = SECTOR_OVERRIDES.get(ticker, sector or “Other”)
tickers[ticker + “.DE”] = (name[:40], sector)
except Exception as e:
print(f”  ⚠  Wikipedia scrape failed for {index_name}: {e}”)
# fallback: always include these core tickers
if len(tickers) < 10:
for t, info in SECTOR_OVERRIDES.items():
if t+”.DE” not in tickers:
tickers[t+”.DE”] = (t, info)
return tickers

def compute_ema(series: pd.Series, span: int) -> pd.Series:
return series.ewm(span=span, adjust=False).mean()

def relative_strength(stock_ret: pd.Series, bench_ret: pd.Series) -> float:
common = stock_ret.index.intersection(bench_ret.index)
if len(common) < 30:
return 50.0
sp = (1 + stock_ret.loc[common]).prod() - 1
bp = (1 + bench_ret.loc[common]).prod() - 1
ratio = (1 + sp) / (1 + bp) - 1
return round(max(0, min(100, 50 + ratio * 200)), 1)

def setup_strength(dist_pct, rs, vol_ratio, pullback_pct, wave1_gain) -> float:
dist_score = max(0, 100 - dist_pct * 6)
composite  = (
dist_score  * 0.30 +
rs          * 0.30 +
min(100, vol_ratio*50) * 0.10 +
min(100, wave1_gain*1.2) * 0.15 +
min(100, pullback_pct*2) * 0.15
)
return round(composite, 1)

def fetch_and_analyse(ticker: str, name: str, sector: str,
dax_daily: pd.Series) -> dict | None:
try:
tk = yf.Ticker(ticker)

```
    weekly = tk.history(period="2y", interval="1wk")
    if weekly.empty or len(weekly) < EMA_WEEKS + 5:
        return None
    weekly_close = weekly["Close"].dropna()

    ema40w        = compute_ema(weekly_close, EMA_WEEKS).iloc[-1]
    current_price = weekly_close.iloc[-1]

    dist_pct = ((current_price - ema40w) / ema40w) * 100
    if not (MIN_DIST_PCT <= dist_pct <= MAX_DIST_PCT):
        return None

    # wave 1
    lookback   = weekly_close.iloc[-52:] if len(weekly_close) >= 52 else weekly_close
    w1_low     = lookback.min()
    w1_high    = lookback.max()
    wave1_gain = ((w1_high - w1_low) / w1_low) * 100
    if wave1_gain < MIN_WAVE1_GAIN:
        return None

    recent       = lookback.iloc[lookback.argmax():]
    if len(recent) < 2:
        return None
    pullback_low  = recent.min()
    pullback_pct  = ((w1_high - pullback_low) / w1_high) * 100
    if pullback_pct < MIN_PULLBACK_PCT:
        return None

    # daily
    daily = tk.history(period="1y", interval="1d")
    if daily.empty:
        return None
    vol_today  = daily["Volume"].iloc[-1]
    vol_avg    = daily["Volume"].tail(VOLUME_DAYS).mean()
    vol_ratio  = vol_today / vol_avg if vol_avg else 1.0
    high_52w   = daily["Close"].tail(252).max()

    # RS
    stock_ret = daily["Close"].pct_change().dropna()
    rs = relative_strength(stock_ret, dax_daily)

    score = setup_strength(dist_pct, rs, vol_ratio, pullback_pct, wave1_gain)

    # sparkline — last CHART_WEEKS weekly closes
    chart_data = [round(float(v),2) for v in weekly_close.iloc[-CHART_WEEKS:].tolist()]

    return {
        "ticker":       ticker.replace(".DE",""),
        "name":         name,
        "sector":       sector,
        "price":        round(float(current_price), 2),
        "ema40w":       round(float(ema40w), 2),
        "dist_pct":     round(dist_pct, 1),
        "wave1_gain":   round(wave1_gain, 1),
        "wave1_low":    round(float(w1_low), 2),
        "wave1_high":   round(float(w1_high), 2),
        "pullback_low": round(float(pullback_low), 2),
        "pullback_pct": round(pullback_pct, 1),
        "high_52w":     round(float(high_52w), 2),
        "rs":           rs,
        "vol_ratio":    round(vol_ratio, 2),
        "setup_score":  score,
        "chart_data":   chart_data,
    }
except Exception as e:
    return None


def main():
console = Console()
run_date = datetime.date.today().isoformat()


console.print(f"\n[bold cyan]🇩🇪  German Wave-2 Scanner[/bold cyan]  [dim]{run_date}[/dim]\n")

# ── discover universe ──────────────────────────────────────────────────
console.print("[dim]Discovering tickers from Wikipedia (DAX/MDAX/SDAX/TecDAX)…[/dim]")
universe = scrape_tickers_from_wikipedia()
console.print(f"[dim]→ {len(universe)} tickers found[/dim]\n")

# ── DAX benchmark ──────────────────────────────────────────────────────
console.print("[dim]Fetching DAX benchmark…[/dim]")
try:
    dax_daily = yf.Ticker("^GDAXI").history(period="1y", interval="1d")["Close"].pct_change().dropna()
except Exception as e:
    console.print(f"[red]DAX fetch failed: {e}[/red]")
    sys.exit(1)

# ── scan ───────────────────────────────────────────────────────────────
results = []
total = len(universe)
for i, (ticker, (name, sector)) in enumerate(universe.items(), 1):
    console.print(f"  [{i:03d}/{total}] [dim]{ticker:12s}[/dim] {name[:30]}")
    r = fetch_and_analyse(ticker, name, sector, dax_daily)
    if r:
        results.append(r)

results.sort(key=lambda x: x["setup_score"], reverse=True)

# ── save JSON ──────────────────────────────────────────────────────────
payload = {"run_date": run_date, "universe_size": total, "results": results}
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
console.print(f"\n[bold green]✓  data.json saved — {len(results)} setups from {total} stocks[/bold green]")

if not results:
    console.print("[yellow]No stocks matched today. Try loosening MAX_DIST_PCT.[/yellow]\n")
    return

# ── terminal table ─────────────────────────────────────────────────────
t = Table(box=box.SIMPLE_HEAD, header_style="dim", padding=(0,1))
t.add_column("TICKER",   style="bold white", no_wrap=True)
t.add_column("NAME",     style="dim")
t.add_column("PRICE",    justify="right")
t.add_column("40W EMA",  justify="right", style="yellow")
t.add_column("Δ EMA",    justify="right")
t.add_column("RS",       justify="right")
t.add_column("W1",       justify="right", style="dim")
t.add_column("PULLBACK", justify="right", style="dim")
t.add_column("VOL/AVG",  justify="right")
t.add_column("SCORE",    justify="right")

dc = lambda v: "bold cyan" if v<4 else "bold green" if v<7 else "bold yellow" if v<11 else "white"
rc = lambda v: "bold cyan" if v>=85 else "bold green" if v>=70 else "yellow" if v>=55 else "white"
sc = lambda v: "bold cyan" if v>=85 else "bold green" if v>=75 else "yellow" if v>=65 else "white"
vc = lambda v: "bold green" if v>=1.5 else "green" if v>=1.1 else "white"

for r in results:
    t.add_row(
        r["ticker"], r["name"][:22],
        f"€{r['price']:.2f}", f"€{r['ema40w']:.2f}",
        Text(f"+{r['dist_pct']:.1f}%", style=dc(r["dist_pct"])),
        Text(str(r["rs"]),             style=rc(r["rs"])),
        f"{r['wave1_gain']:.0f}%",
        f"{r['pullback_pct']:.0f}%",
        Text(f"{r['vol_ratio']:.2f}×", style=vc(r["vol_ratio"])),
        Text(str(r["setup_score"]),    style=sc(r["setup_score"])),
    )
console.print(t)

top = results[0]
console.print(f"[bold cyan]Top pick:[/bold cyan] {top['ticker']} — Score {top['setup_score']}, +{top['dist_pct']}% above 40W EMA, RS {top['rs']}\n")


if **name** == “**main**”:
main()
