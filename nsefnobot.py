from tradingview_ta import TA_Handler, Interval, Exchange
import json
import sys
from datetime import datetime, timedelta
import pytz


log_path = "bot_log.txt"

def get_time():
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz)

now = get_time()
one_hour_later =now + timedelta(hours=1)
next_run = one_hour_later.strftime("[ %H : %M ] %m-%d")



if len(sys.argv) > 1:
    file_path_arg = sys.argv[1]
    json_path = file_path_arg
    print("using sys.argv - " + file_path_arg)
else:
    json_path = "all_stock_data.json"


long_rsi = 60
short_rsi = 40

long_exit_rsi = 55
short_exit_rsi = 45

def get_timestamp():
    india_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(india_tz).strftime('%m-%d %H:%M')

def ptc_diff(num1, num2):
    try:
        return ((num1 - num2) / num2) * 100
    except Exception as e:
        log(f"Error in ptc_diff: {e}")
        return 0

def load_data():
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

def log(msg):
    content = f"{msg}\n\n"
    with open(log_path, "a") as f:
        f.write(content)

with open(log_path, "w") as f:
    f.write(f"\n{get_timestamp()} Next: {next_run} =>\n")


def get_data(sym, screener = "INDIA", exchange = "NSE"):
    try:
        handler = TA_Handler(
            symbol=sym,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_HOUR
        )
        analysis = handler.get_analysis()
        return round(analysis.indicators["RSI"],2), round(analysis.indicators["close"],2)
    except Exception as e:
        log(f"Error fetching recommendation: {e}")
        return None, None

def main():
    total_data = load_data()
    if 'active' not in total_data:
        total_data['active'] = {}
    if 'closed' not in total_data:
        total_data['closed'] = []

    for stock,data in total_data['active'].items():
        if stock == "BTCUSD":
            rsi, price = get_data(stock, "CRYPTO", "BITSTAMP")
        else:
            rsi, price = get_data(stock)

        if rsi is not None and price is not None and len(data) == 0:
            if rsi > long_rsi:
                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": 1,
                    "entry": price,
                    "rsi":[rsi],
                    "profit%": 0
                }
                log(f"New LONG: {stock} at price {price} rsi {rsi}")
            elif rsi < short_rsi:
                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": -1,
                    "entry": price,
                    "rsi":[rsi],
                    "profit%": 0
                }
                log(f"New SHORT: {stock} at price {price} rsi {rsi}")

            else:
                pass
        elif rsi is not None and price is not None and len(data) > 0:
            current_position = data["position"]
            if current_position > 0 and rsi < long_exit_rsi:
                current_profit = ptc_diff(price, data["entry"])*current_position
                profit = data["profit%"] + current_profit
                total_data["closed"].append({
                    "stock": stock,
                    "timestamp": get_timestamp(),
                    "position":data['position'],
                    "entry": data["entry"],
                    "exit": price,
                    "rsi":data["rsi"],
                    "profit%": current_profit
                    })


                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": 0,
                    "entry": price,
                    "rsi":[],
                    "profit%": profit
                }
                log(f"Exited LONG: {stock} - ({profit:.2f}%)")
            elif current_position < 0 and rsi > short_exit_rsi:
                current_profit = ptc_diff(price, data["entry"])*current_position
                profit = data["profit%"] + current_profit
                total_data["closed"].append({
                    "stock": stock,
                    "timestamp": get_timestamp(),
                    "position":data['position'],
                    "entry": data["entry"],
                    "exit": price,
                    "rsi":data["rsi"],
                    "profit%": current_profit
                    })
                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": 0,
                    "entry": price,
                    "rsi":[],
                    "profit%": profit
                }
                log(f"Exited SHORT {stock} - ({profit:.2f}%)")
            elif current_position == 0 and rsi > long_rsi:
                profit = data["profit%"]
                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": 1,
                    "entry": price,
                    "rsi":[rsi],
                    "profit%": profit
                }
                log(f"New LONG: {stock} at price {price} rsi {rsi}")

            elif current_position == 0 and rsi < short_rsi:
                profit = data["profit%"]
                total_data["active"][stock] = {
                    "timestamp": get_timestamp(),
                    "position": -1,
                    "entry": price,
                    "rsi":[rsi],
                    "profit%": profit
                }
                log(f"New SHORT: {stock} at price {price} rsi {rsi}")

            else:
                profit = ptc_diff(price, data["entry"])*current_position
                data["rsi"].append(rsi)
                total_data["active"][stock] = {
                    "timestamp": data["timestamp"],
                    "position": data["position"],
                    "entry": data["entry"],
                    "rsi": data["rsi"],
                    "profit%": data["profit%"]
                }
                log(f"Holding: {stock} - profit: ({profit:.2f}%)\n position: {data['position']}|Current price: {price} rsi: {rsi}|Entry: {data['entry']}")

        else:
            log(f"error for {stock}")

    save_data(total_data)


if __name__ == "__main__":
    main()
