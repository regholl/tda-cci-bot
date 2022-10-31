# This file contains all the functions that hook up to the TD Ameritrade API

# Import packages

import datetime as dt
from db import *
import json
import numpy as np
import pandas as pd
import pytz
import requests
import time

# Global variables

utc = pytz.timezone('UTC')
local_timezone = pytz.timezone('US/Pacific')
tda_base = 'https://api.tdameritrade.com'

# TDA functions

def tda_authenticate():
    deta = connect_db()
    db_config = deta.Base("db_config")
    items = db_config.fetch().items
    if items == []:
        create_database(db_config, name="config")
        time.sleep(2)
        deta = connect_db()
        db_config = deta.Base("db_config")
    tda_access_limit = int(db_config.get("TDA_ACCESS_LIMIT")['value'])
    tda_refresh = db_config.get("TDA_REFRESH")['value']
    tda_api = db_config.get("TDA_API")['value']
    tda_account = db_config.get("TDA_ACCOUNT")['value']
    access_time_adj = int(tda_access_limit * 0.9)
    tda_access_last = pd.Timestamp(db_config.get("TDA_LAST_ACCESS")['value'], tz=utc).astimezone(local_timezone)
    tda_payload = {
        'grant_type': 'refresh_token',
        'refresh_token': tda_refresh,
        'client_id': tda_api,
    }
    tda_auth_url = '{}/v1/oauth2/token'.format(tda_base)
    now_time = dt.datetime.now(tz=local_timezone)
    minutes_since_refresh = round((now_time - tda_access_last).total_seconds() / 60, 2)
    if minutes_since_refresh > access_time_adj:
        tda_token_request = requests.post(tda_auth_url, data = tda_payload)
        tda_token_response = json.loads(tda_token_request.content)
        tda_access_token = tda_token_response['access_token']
        put_keys = ["TDA_ACCESS", "TDA_LAST_ACCESS"]
        put_values = [tda_access_token, dt.datetime.now(tz=utc).strftime("%Y-%m-%d %X")]
        for i in range(len(put_keys)):
            entry = {
                "key": put_keys[i],
                "value": put_values[i]
            }
            db_config.put(entry)
    else:
        tda_access_token = db_config.get("TDA_ACCESS")['value']
    tda_headers = {'Authorization': 'Bearer {}'.format(tda_access_token)}
    auth_dict = {
        "account_nbr": tda_account,
        "api_key": tda_api,
        "headers": tda_headers,
    }
    return auth_dict

def get_quote_tda(symbol="SPY"):
    auth = tda_authenticate()
    quote_url = f"{tda_base}/v1/marketdata/quotes?apikey={auth['api_key']}&symbol={symbol}"
    req = requests.get(quote_url, headers = auth["headers"])
    resp = json.loads(req.content)
    return resp

def get_data_tda(ticker="SPY", periodType="day", period=10, frequencyType="minute", frequency=30, extended_hours=False):
    periodTypes = ["day", "month", "year", "ytd"]
    period_day = [1, 2, 3, 4, 5, 10]
    period_month = [1, 2, 3, 6]
    period_year = [1, 2, 3, 5, 10, 15, 20]
    period_ytd = [1]
    frequencyType_day = ["minute"]
    frequencyType_month = ["daily", "weekly"]
    frequencyType_year = ["daily", "weekly", "monthly"]
    frequencyType_ytd = ["daily", "weekly"]
    frequency_minute = [1, 5, 10, 15, 30]
    frequency_daily = [1]
    frequency_weekly = [1]
    frequency_monthly = [1]
    factor = 1
    if frequencyType in ["daily", "weekly", "monthly"] and frequency != 1:
        factor = frequency
        frequency = 1
    if frequencyType == "hour":
        frequencyType = "minute"
        frequency = int(frequency * 60)
    if frequencyType == "minute" and frequency not in frequency_minute:
        freq_min_rev = list(reversed(frequency_minute))
        i = 0
        while i < len(freq_min_rev):
            if frequency % freq_min_rev[i] == 0:
                factor = int(frequency / freq_min_rev[i])
                frequency = freq_min_rev[i]
                break
            i += 1
    # ext = False
    useEpoch = False
    now = dt.datetime.now()
    epoch = dt.datetime.utcfromtimestamp(0)
    # now = dt.datetime.now(tz=utc)
    # epoch = pd.Timestamp(dt.datetime.utcfromtimestamp(0),tz=utc)
    epoch_now_diff = now - epoch
    epoch_to_now = epoch_now_diff.days * 24 * 60 * 60 * 1000 + (epoch_now_diff.seconds * 1000) + (int(epoch_now_diff.microseconds / 1000))
    then = now - dt.timedelta(days=1)
    epoch_then_diff = then - epoch
    epoch_to_then = epoch_then_diff.days * 24 * 60 * 60 * 1000 + (epoch_then_diff.seconds * 1000) + (int(epoch_then_diff.microseconds / 1000))
    startDate = epoch_to_then
    endDate = epoch_to_now
    auth = tda_authenticate()
    data_url = f"{tda_base}/v1/marketdata/{ticker}/pricehistory?apikey={auth['api_key']}&frequencyType={frequencyType}&frequency={frequency}&needExtendedHoursData={extended_hours}&endDate={endDate}"
    if useEpoch:
        data_url = data_url + f"&startDate={startDate}"
    else:
        data_url = data_url + f"&periodType={periodType}&period={period}"
    req = requests.get(data_url, headers = auth["headers"])
    resp = json.loads(req.content)
    if 'candles' not in resp:
        print(resp)
    bars = resp['candles']
    if bars[-1]['close'] == 0:
        bars = bars[:-1]
    if factor != 1:
        if frequencyType == "minute" and frequency == 30:
            if factor == 2:
                bar_hour_starts_utc = ["13:30", "14:30", "15:30", "16:30", "17:30", "18:30", "19:30"]
            elif factor == 4:
                bar_hour_starts_utc = ["13:30", "15:30", "17:30", "19:30"]
            elif factor == 6:
                bar_hour_starts_utc = ["13:30", "16:30", "19:30"]
            elif factor == 8:
                bar_hour_starts_utc = ["13:30", "17:30"]
            elif factor == 10:
                bar_hour_starts_utc = ["13:30", "18:30"]
            elif factor == 12:
                bar_hour_starts_utc = ["13:30", "19:30"]
            bars_hour = []
            bars_Xmin = []
            highs_Xmin = []
            lows_Xmin = []
            volumes_Xmin = []
            for bar in bars:
                timestampX = pd.to_datetime(int(bar['datetime']) * 1000000)
                hourX = timestampX.strftime("%H:%M")
                if hourX in bar_hour_starts_utc and len(bars_Xmin) > 0:
                    highs_Xmin = []
                    lows_Xmin = []
                    volumes_Xmin = []
                    for barX in bars_Xmin:
                        highs_Xmin.append(barX['high'])
                        lows_Xmin.append(barX['low'])
                        volumes_Xmin.append(barX['volume'])
                    highX = max(highs_Xmin)
                    lowX = min(lows_Xmin)
                    volumeX = sum(volumes_Xmin)
                    openX = bars_Xmin[0]['open']
                    closeX = bars_Xmin[len(bars_Xmin)-1]['close']
                    bar_hour = {
                        "timestamp": timestampX,
                        "datetime": bar['datetime'],
                        "open": openX,
                        "high": highX,
                        "low": lowX,
                        "close": closeX,
                        "volume": volumeX,
                    }
                    bars_hour.append(bar_hour)
                    bars_Xmin = []
                bars_Xmin.append(bar)
            bars = bars_hour
        else:
            bars_revised = []
            bars_X = []
            highs_X = []
            lows_X = []
            volumes_X = []
            counter = 0
            for bar in bars:
                timestampX = pd.to_datetime(int(bar['datetime']) * 1000000)
                if counter == factor and len(bars_X) > 0:
                    highs_X = []
                    lows_X = []
                    volumes_X = []
                    for barX in bars_X:
                        highs_X.append(barX['high'])
                        lows_X.append(barX['low'])
                        volumes_X.append(barX['volume'])
                    highX = max(highs_X)
                    lowX = min(lows_X)
                    volumeX = sum(volumes_X)
                    openX = bars_X[0]['open']
                    closeX = bars_X[len(bars_X)-1]['close']
                    bar_revised = {
                        "timestamp": timestampX,
                        "datetime": bar['datetime'],
                        "open": openX,
                        "high": highX,
                        "low": lowX,
                        "close": closeX,
                        "volume": volumeX,
                    }
                    bars_revised.append(bar_revised)
                    bars_X = []
                    counter = 0
                bars_X.append(bar)
                counter += 1
            bars = bars_revised
    return bars

def get_positions_tda():
    auth = tda_authenticate()
    tda_account_url = '{}/v1/accounts/{}'.format(tda_base, auth['account_nbr'])
    tda_positions_url = '{}?fields=positions'.format(tda_account_url)
    tda_positions_request = requests.get(tda_positions_url, headers = auth['headers'])
    tda_positions_content = json.loads(tda_positions_request.content)
    positions = []
    if 'securitiesAccount' not in tda_positions_content:
        positions = positions
        # print(tda_positions_content)
    if 'positions' in tda_positions_content['securitiesAccount']:
        positions = tda_positions_content['securitiesAccount']['positions']
    # else:
    #     positions = [{
    #         "instrument": {
    #             "symbol": "None"
    #         },
    #         "longQuantity": 0,
    #         "shortQuantity": 0,
    #         "averagePrice": 0,
    #         "marketValue": 0,
    #         "currentDayProfitLossPercentage": 0
    #     }]
    if positions != [] and "instrument" not in list(positions[0].keys()):
        positions = positions
        # print(positions)
    return positions

def get_orders_tda():
    auth = tda_authenticate()
    tda_history_url = '{}/v1/accounts/{}/transactions'.format(tda_base, auth['account_nbr'])
    tda_history_request = requests.get(tda_history_url, headers = auth['headers'])
    tda_history_content = json.loads(tda_history_request.content)
    orders = []
    if len(tda_history_content) < 1:
        orders = [{
            "orderDate": "1/1/2000 12:00:00",
            "transactionItem": {
                "instrument": {
                    "symbol": "none"
                },
                "instruction": "none",
                "amount": 0,
                "price": 0
            }
        }]
    else:
        orders = [item for item in tda_history_content if item['type'] == 'TRADE']
    orders = [item for item in orders if "orderDate" in list(item.keys())]
    orders = [item for item in orders if "transactionItem" in list(item.keys())]
    orders = [item for item in orders if "instrument" in list(item["transactionItem"].keys())]
    return orders

def get_orders2_tda():
    auth = tda_authenticate()
    tda_account_url = '{}/v1/accounts/{}'.format(tda_base, auth['account_nbr'])
    tda_orders_url = '{}?fields=orders'.format(tda_account_url)
    tda_orders_request = requests.get(tda_orders_url, headers = auth['headers'])
    tda_orders_content = json.loads(tda_orders_request.content)
    orders = []
    if 'securitiesAccount' not in tda_orders_content:
        orders = orders
        # print(tda_orders_content)
    if 'orderStrategies' not in tda_orders_content['securitiesAccount']:
        orders = orders
        # print(tda_orders_content['securitiesAccount'])
    else:
        orders = tda_orders_content['securitiesAccount']['orderStrategies']
    return orders

def get_hours_tda():
    auth = tda_authenticate()
    # market_date = dt.datetime.now().strftime('%Y-%m-%d')
    # tda_hours_url = '{}/v1/marketdata/EQUITY/hours?apikey={}&date={}'.format(tda_base, auth['api_key'], market_date)
    # tda_hours_content = json.loads(requests.get(tda_hours_url, headers = auth['headers']).content)
    # market_open = pd.to_datetime(tda_hours_content['equity']['EQ']['sessionHours']['regularMarket'][0]['start'])
    # market_close = pd.to_datetime(tda_hours_content['equity']['EQ']['sessionHours']['regularMarket'][0]['end'])
    # if market_close > dt.datetime.now(tz=local_timezone) > market_open:
    #     market_is_open = True
    # else:
    #     market_is_open = False
    # return market_is_open
    current_time = dt.datetime.now(tz=local_timezone)
    market = "EQUITY"
    tda_hours_url = '{}/v1/marketdata/{}/hours?apikey={}'.format(tda_base, market, auth['api_key'])
    tda_hours_request = requests.get(tda_hours_url, headers = auth['headers'])
    if tda_hours_request.status_code != 200:
        tda_hours_content = tda_hours_request.content
        print(tda_hours_content)
        closing_time = current_time
        market_is_open = False
    else:
        tda_hours_content = json.loads(tda_hours_request.content)
        if 'EQ' in list(tda_hours_content['equity'].keys()):
            closing_time = pd.to_datetime(tda_hours_content['equity']['EQ']['sessionHours']['regularMarket'][0]['end']).astimezone(local_timezone)
            market_is_open = tda_hours_content['equity']['EQ']['isOpen']
        else:
            closing_time = current_time
            market_is_open = False
    return (market_is_open, closing_time, current_time)

def get_chain_tda(ticker):
    result = {}
    contract_type = "ALL" # ALL (default), CALL, PUT
    tickers_db = connect_db().Base("tickers_db")
    delta_min = int(tickers_db.get(ticker)['delta_min'])
    # delta_min = 90
    strike_count = 3
    from50 = np.round(abs(1 - delta_min / 50), 2)
    while from50 > 0:
        strike_count += 2
        from50 = np.round(from50 - 0.05, 2)
    moneyness = "ALL" # ITM, NTM, OTM, SAK, SBK, SNK, ALL
    now = dt.datetime.now()
    dte_min = int(tickers_db.get(ticker)['dte_min'])
    from_date = (now - dt.timedelta(days=dte_min)).strftime("%Y-%m-%d")
    to_date = (now + dt.timedelta(days=dte_min+32)).strftime("%Y-%m-%d")
    auth = tda_authenticate()
    chain_url = f'{tda_base}/v1/marketdata/chains?apikey={auth["api_key"]}&symbol={ticker}&contractType={contract_type} \
                &includeQuotes=false&strikeCount={strike_count}&range={moneyness}&fromDate={from_date}&toDate={to_date} \
                &optionType=S'
    tda_chain_request = requests.get(chain_url, headers = auth['headers'])
    if tda_chain_request.status_code != 200:
        print("Error: TDA status code")
        tda_chain_content = tda_chain_request.content
    else:
        tda_chain_content = json.loads(tda_chain_request.content)
        if tda_chain_content['status'] != 'FAILED':
            calls = tda_chain_content['callExpDateMap']
            call_exps = list(calls.keys())
            call_exp = call_exps[0]
            call_strikes = list(calls[call_exp].keys())
            call_strikes = list(reversed(call_strikes))
            call_strike = 0
            i = 0
            while i < len(call_strikes):
                call = calls[call_exp][call_strikes[i]][0]
                call_delta = np.round(abs(float(call['delta'])) * 100)
                if call_delta > delta_min:
                    call_strike = call_strikes[i]
                    break
                i += 1
            puts = tda_chain_content['putExpDateMap']
            put_exps = list(puts.keys())
            put_exp = put_exps[0]
            put_strikes = list(puts[put_exp].keys())
            put_strike = 0
            i = 0
            while i < len(put_strikes):
                put = puts[put_exp][put_strikes[i]][0]
                put_delta = np.round(abs(float(put['delta'])) * 100)
                if put_delta > delta_min:
                    put_strike = put_strikes[i]
                    break
                i += 1
            
    result = {
        "put": put['symbol'],
        "call": call['symbol']
    }
    return result

def tda_submit_order(instruction, quantity, symbol, assetType="OPTION", orderType="MARKET", limit_price=0):
    auth = tda_authenticate()
    tda_orders_url = '{}/v1/accounts/{}/orders'.format(tda_base, auth['account_nbr'])
    if "_" not in symbol:
        assetType = "EQUITY"
        if instruction == "SELL_TO_OPEN":
            instruction = "SELL_SHORT"
        elif instruction == "BUY_TO_CLOSE":
            instruction = "BUY_TO_COVER"
        elif instruction == "BUY_TO_OPEN":
            instruction = "BUY"
        elif instruction == "SELL_TO_CLOSE":
            instruction = "SELL"
    data = {
        "orderType": orderType, # MARKET or LIMIT
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": instruction,
                "quantity": quantity,
                "instrument": {
                    "symbol": symbol,
                    "assetType": assetType # EQUITY or OPTION
                }
            }
        ]
    }
    if orderType == "LIMIT" and float(limit_price) != 0:
        data["price"] = str(limit_price)
    r = requests.post(tda_orders_url, json=data, headers = auth['headers'])
    if r.status_code in [200, 201]:
        print(f"{r.status_code}: {r.content}")
        return r.content
    else:
        print(f"{r.status_code}: {json.loads(r.content)}")
        return json.loads(r.content)

def get_watchlist_tda(name="default"):
    auth = tda_authenticate()
    url = f"{tda_base}/v1/accounts/{auth['account_nbr']}/watchlists"
    r = requests.get(url, headers = auth['headers'])
    resp = json.loads(r.content)
    wl = [item for item in resp if item['name'] == name][0]
    items = wl['watchlistItems']
    symbols = [item['instrument']['symbol'] for item in items]
    return symbols