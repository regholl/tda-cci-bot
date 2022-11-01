# This file contains a function to connects to our Deta base

# Import required packages

from deta import Deta
from dotenv import load_dotenv
import os

# Connect to Deta Base

def connect_db():
    if ".env" in os.listdir():
        env = load_dotenv(".env")
        DETA_KEY = os.getenv("DETA_KEY")
    else:
        DETA_KEY = os.environ["DETA_KEY"]
    deta = Deta(DETA_KEY)
    return deta

def create_database(db_info, name="config", symbols=None):
    config_keys = ["TDA_API", "TDA_REFRESH", "TDA_ACCOUNT"]
    config_values = [os.getenv(key) for key in config_keys]
    config_keys = config_keys + ["TDA_ACCESS", "TDA_LAST_ACCESS", "TDA_LAST_REFRESH", "TDA_ACCESS_LIMIT", "BOT_ON"]
    config_values = config_values + ["asfdasdf", "8/8/2022 20:54:30", "8/18/2022 19:08:26", "30", True]
    user_keys = ["josh", "tyler"]
    user_values = ["cci", "tda"]
    settings_keys = ["timeframe", "ticker", "watchlist", "shares", "cciLength", "cciAvgLength", "over_sold", "over_bought"]
    settings_values = ["10m", "SPY", "default", 1, 14, 9, -100, 100]
    if symbols == None:
        symbols = ["SPY", "QQQ"]
    ticker_keys = list(range(len(symbols)))
    if name == "config":
        for i in range(len(user_keys)):
            entry = {
                "key": user_keys[i],
                "value": user_values[i]
            }
            db_info.put(entry)
    elif name == "users":
        for i in range(len(config_keys)):
            entry = {
                "key": config_keys[i],
                "value": config_values[i]
            }
            db_info.put(entry)
    elif name == "tickers":
        for i in range(len(ticker_keys)):
            entry = {
                "key": str(ticker_keys[i]),
                "value": symbols[i]
            }
            db_info.put(entry)
    elif name == "settings":
        for i in range(len(settings_keys)):
            entry = {
                "key": settings_keys[i],
                "value": settings_values[i]
            }
            db_info.put(entry)