from flask import Flask, jsonify
import requests
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

trade_signal = {"status": "No trade available"}  # Default message

def fetch_nifty_options():
    global trade_signal
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain",
        "Connection": "keep-alive",
    }

    session = requests.Session()  # Maintain session for NSE
    session.headers.update(headers)

    try:
        # First request to establish session (important)
        session.get("https://www.nseindia.com", timeout=5)

        # Fetch option chain data
        response = session.get(url, timeout=10)
        data = response.json()

        # Extract Option Chain Data
        records = data.get("records", {}).get("data", [])

        # Analyze Open Interest (OI) and PCR
        call_oi = sum([r.get("CE", {}).get("openInterest", 0) for r in records])
        put_oi = sum([r.get("PE", {}).get("openInterest", 0) for r in records])
        pcr = round(put_oi / call_oi, 2) if call_oi else 0

        # Generate Trade Signal
        if pcr > 1.3:
            trade_signal = {"status": "BUY NIFTY CALL", "PCR": pcr}
        elif pcr < 0.8:
            trade_signal = {"status": "BUY NIFTY PUT", "PCR": pcr}
        else:
            trade_signal = {"status": "No trade available", "PCR": pcr}

    except Exception as e:
        trade_signal = {"error": str(e)}

# Scheduler to run every 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_nifty_options, "interval", minutes=5)
scheduler.start()

@app.route("/")
def home():
    return jsonify(trade_signal)

if __name__ == "__main__":
    fetch_nifty_options()  # Run once at startup
    app.run(host="0.0.0.0", port=5000)