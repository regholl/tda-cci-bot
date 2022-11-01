# This file runs our strategy in the background

# Import required packges

import datetime as dt
from db import *
import pytz
import ta
from tda import *
import time

# Global variables

log_count = 0
error_streak = 0
bot_on_last = False
utc = pytz.timezone("UTC")
local_timezone = pytz.timezone("US/Pacific")

def run():

    # Measure speed

    time_start = time.time()

    # Check if bot is on

    deta = connect_db()
    db_config = deta.Base("db_config")
    bot_on = bool(db_config.get("BOT_ON")['value'])
    global bot_on_last
    if bot_on_last == True and bot_on == False:
        print("Bot turning off")
    elif bot_on_last == False and bot_on == True:
        print("Bot turning on")
    bot_on_last = bot_on
    if bot_on == False:
        return False

    # Error counter

    global error_streak
    error_streak += 1

    # Connect to database

    db_settings = deta.Base("db_settings")
    ticker = db_settings.get("ticker")['value']
    timeframe = db_settings.get("timeframe")['value']
    shares = db_settings.get("shares")['value']
    cciLength = db_settings.get("cciLength")['value']
    cciAvgLength = db_settings.get("cciAvgLength")['value']
    over_sold = db_settings.get("over_sold")['value']
    over_bought = db_settings.get("over_bought")['value']

    # Adjust timeframe

    if "m" in timeframe:
        frequencyType = "minute"
        frequency = int(timeframe.replace("m",""))
        periodType = "day"
        period = 2
    elif "h" in timeframe:
        frequencyType = "minute"
        frequency = np.round(int(timeframe.replace("h","")) * 60, 0)
        periodType = "day"
        period = 10
    elif "D" in timeframe:
        frequencyType = "daily"
        frequency = 1
        periodType = "month"
        period = 3
    else:
        print("Error: Unknown timeframe")

    # Get data

    data = get_data_tda(ticker = ticker, periodType = periodType, period = period, frequencyType = frequencyType, frequency = frequency)
    df = pd.DataFrame()
    if frequencyType == "minute":
        time_format = "%m/%d %H:%M"
    elif frequencyType == "daily":
        time_format = "%m/%d"
    elif frequencyType == "weekly":
        time_format = "%m/%d/%Y"
    elif frequencyType == "monthly":
        time_format = "%b %Y"
    tda_times = [candle['datetime'] for candle in data]
    tda_dates = [dt.datetime.utcfromtimestamp(time_ / 1000) for time_ in tda_times]
    tda_locals = [utc.localize(date).astimezone(local_timezone) for date in tda_dates]
    tda_datetimes = [time_.strftime(time_format) for time_ in tda_locals]
    tda_opens = [item['open'] for item in data]
    tda_highs = [item['high'] for item in data]
    tda_lows = [item['low'] for item in data]
    tda_closes = [item['close'] for item in data]
    df['datetime'] = tda_datetimes
    df['open'] = tda_opens
    df['high'] = tda_highs
    df['low'] = tda_lows
    df['close'] = tda_closes

    # Calculate CCI

    CCI = ta.trend.cci(df['high'], df['low'], df['close'], window = cciLength)
    df['CCI'] = CCI
    CCIAvg = df['CCI'].rolling(window = cciAvgLength).mean()

    # Get market status

    hours = get_hours_tda()
    market_open = hours[0]
    closing_time = hours[1]
    # current_time = hours[2]

    # Get signals

    current_time = dt.datetime.now(tz=local_timezone)
    minutes_until_close = np.round((closing_time - current_time).total_seconds() / 60, 2)
    CCI_values = list(CCI.values)
    CCIAvg_values = list(CCIAvg.values)
    signal = "Neutral"
    if 0 < minutes_until_close < 450:
        if CCI_values[-2] > CCIAvg_values[-2]:
            signal = "Sell"
        elif CCI_values[-2] > CCIAvg_values[-2]:
            signal = "Buy"
    else:
        if CCI_values[-1] > CCIAvg_values[-1]:
            signal = "Sell"
        elif CCI_values[-1] < CCIAvg_values[-1]:
            signal = "Buy"

    # Get positions

    positions = get_positions_tda()
    if positions != []:
        tickers_held = [position['instrument']['symbol'] for position in positions]
        long_shares = [int(position['longQuantity']) for position in positions]
        short_shares = [int(position['shortQuantity']) for position in positions]
        quantities = list(np.array(long_shares) - np.array(short_shares))
    else:
        tickers_held = []
        long_shares = []
        short_shares = []
        quantities = []
    quantities = [int(abs(qty)) for qty in quantities]
    ticker_qty_dict = dict(zip(tickers_held, quantities))

    # Get watchlist

    symbols = get_watchlist_tda()
    if ticker not in symbols:
        print("Ticker not in watchlist")
        in_watchlist = False
    else:
        in_watchlist = True

    # Get orders

    orders = get_orders2_tda()
    open_orders = [order for order in orders if order['status'] in ["PENDING_ACTIVATION", "QUEUED", "WORKING"]]
    open_tickers = [order['orderLegCollection'][0]['instrument']['symbol'] for order in open_orders]

    # Exit order

    if 0 < minutes_until_close < 450 \
    and ticker in tickers_held \
    and ticker not in open_tickers \
    and signal == "Sell":
        qty = ticker_qty_dict[ticker]
        tda_submit_order("SELL", qty, ticker)
        tickers_held.remove(ticker)

    # Entry order

    if 0 < minutes_until_close < 450 \
    and ticker not in tickers_held \
    and ticker not in open_tickers \
    and in_watchlist \
    and signal == "Buy":
        tda_submit_order("BUY", shares, ticker)

    # Print log

    now = dt.datetime.now(tz=local_timezone).strftime("%Y-%m-%d %X")
    time_end = time.time()
    time_total = np.round(time_end - time_start, 2)
    global log_count
    log_count += 1
    if log_count == 1 or log_count % 50 == 0:
        print_log = [
            ["Time", f" = {now}"],
            ["Market open", f" = {market_open}"],
            ["Execution Speed", f" = {time_total} seconds"],
            ["---------------", "---------------"]
        ]
    else:
        print_log = [
            ["Execution Speed", f" = {time_total} seconds"],
        ]
    for item_list in print_log:
        for i in item_list:
            print(i.ljust(20), end='')
        print()

    # Since the bot made it to the end of the script successfully, reset error streak to 0

    error_streak = 0

    # End run() function

# Run the entire script in a continuous loop

run()
while True:
    if error_streak < 5:
        try:
            run()
        except Exception as e:
            print(e)
            pass
    else:
        run()
    time.sleep(0.01)