import requests

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzNzY5MDYiLCJqdGkiOiI2OTFlMTFhNTFkZTI2NzdiZDkxNjliNTYiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzYzNTc4Mjc3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NjM1ODk2MDB9.4kdLONduaV0yv19y3jSXlo4f19coTub-fiazW3aAxS8"

url = "https://api.upstox.com/v2/option/chain"
params = {
    "instrument_key": "NSE_INDEX|Nifty 50",
    "expiry_date": "2025-11-25"
}
headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

r = requests.get(url, headers=headers, params=params)

print("STATUS:", r.status_code)
print("RAW RESPONSE:")
print(r.text)
