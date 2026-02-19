import pandas as pd
import requests
from datetime import timedelta
import time

# ========= CONFIG =========
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzNzY5MDYiLCJqdGkiOiI2OTk2MDYwZTdhNjRlNzIxOGExZTk5YjQiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcxNDM5NjMwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzE0NTIwMDB9.HD9vD_KxWKH7JtjypH0SaWEUqSBu_uc2M_yUNk80rJs"  # paste your token
INPUT_EXCEL  = "input_times.xlsx"        # your file with Date/Time
OUTPUT_EXCEL = "output_with_nifty.xlsx"  # output file
DATE_COLUMN  = "Date"                    # column name in your Excel
TIME_COLUMN  = "Time"                    # column name in your Excel
INTERVAL     = "1minute"                 # or '5minute'
# ==========================

BASE_URL = "https://api.upstox.com/v2"
HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}

NIFTY_INDEX_KEY = "NSE_INDEX|Nifty 50"


def fetch_nifty_candles(from_date, to_date, interval="1minute"):
    """
    Fetch NIFTY 50 historical candles from Upstox between from_date and to_date.
    from_date / to_date: 'YYYY-MM-DD' strings
    Returns list of candles.
    """
    url = f"{BASE_URL}/historical-candle/{NIFTY_INDEX_KEY}/{interval}/{to_date}/{from_date}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        raise RuntimeError(f"API error {r.status_code}: {r.text}")
    data = r.json()
    candles = data.get("data", {}).get("candles", [])
    return candles


def find_closest_price(candles, target_ts):
    """
    candles: list like [[ts, o, h, l, c, v, oi], ...]
    target_ts: pandas.Timestamp
    Returns close price (float) of closest candle.
    """
    if not candles:
        return None
    df = pd.DataFrame(
        candles,
        columns=["timestamp", "open", "high", "low", "close", "volume", "oi"],
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    target_ts = pd.to_datetime(target_ts)
    if target_ts.tz is not None:
        target_ts = target_ts.tz_localize(None)

    df["diff"] = (df["timestamp"] - target_ts).abs()
    row = df.loc[df["diff"].idxmin()]
    return float(row["close"])


def main():
    # 1) Read Excel and build timestamp
    df = pd.read_excel(INPUT_EXCEL)

    # Expect columns like 'Date' = 2025-10-14, 'Time' = 11:27:00
    df["DateTime"] = pd.to_datetime(df[DATE_COLUMN].astype(str) + " " + df[TIME_COLUMN].astype(str))

    # 2) Work per day to reduce API calls
    df["DateOnly"] = df["DateTime"].dt.date

    all_prices = []

    unique_dates = sorted(df["DateOnly"].unique())
    print(f"Unique trading dates in file: {unique_dates}")

    for d in unique_dates:
        day_mask = df["DateOnly"] == d
        day_times = df.loc[day_mask, "DateTime"]

        day_str = pd.to_datetime(d).strftime("%Y-%m-%d")
        from_date = (pd.to_datetime(d) - timedelta(days=1)).strftime("%Y-%m-%d")
        to_date = day_str

        print(f"\nFetching NIFTY candles for {from_date} -> {to_date} ...")
        candles = fetch_nifty_candles(from_date, to_date, interval=INTERVAL)
        print(f"Got {len(candles)} candles")

        # 3) For each timestamp in this day, find closest price
        for ts in day_times:
            price = find_closest_price(candles, ts)
            all_prices.append(price)

        # polite pause to avoid rate limits
        time.sleep(0.5)

    # 4) Attach prices (order preserved because we iterated in df order)
    df["NIFTY Price"] = all_prices

    # 5) Save to Excel
    df.drop(columns=["DateOnly"], inplace=True)
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"\n✅ Done. Saved to {OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()
