# https://www.ig.com/en-ch/trading-strategies/16-candlestick-patterns-every-trader-should-know-180615
# https://www.dailyfx.com/education/candlestick-patterns/bearish-harami.html
# https://www.leguideboursier.com/apprendre-bourse/analyse-technique/fractales-bills-williams.php
# https://pypi.org/project/candlestick-patterns-subodh101/
import threading
from tradingview_ta import TA_Handler, Interval, Exchange
import json
from talib.abstract import *
from pyiqoptionapi import *
import sys
import datetime
import time
import ta
import os
import operator
import numpy as np
import pandas as pd
import psycopg2
from iqoptionapi.stable_api import IQ_Option
from multiprocessing import Process, Queue, Pool, Manager
from itertools import product
import threading
sys.path.append('E:\\users\houssem\\trading_analysis\\all_indicators')
sys.path.append('E:\\users\houssem\\trading_analysis\\database')
# print(sys.path)
import write_to_db as myDb
import indicators as myModule
from .. import credentials
# I_want_money = IQ_Option(credentials.login, credentials.mdp2)
# I_want_money.connect()


# opcode_data=I_want_money.get_all_ACTIVES_OPCODE()

# instrument_type="digital-option"#"binary-option"/"digital-option"/"forex"/"cfd"/"crypto"
# I_want_money.subscribe_top_assets_updated(instrument_type)


# while True:
#     if I_want_money.get_top_assets_updated(instrument_type)!=None:
#         break

# top_assets=I_want_money.get_top_assets_updated(instrument_type)
# popularity_neg={}
# popularity_pos={}
# print(" *******************test the loop************************")
# allCurrencies = I_want_money.get_all_ACTIVES_OPCODE()
# for asset in top_assets:
#     opcode=asset["active_id"]
    
#     popularity_value=asset["diff_1h"]["value"]
#     if (popularity_value > 0):
#         volatility_value_positive=popularity_value
#     else :
#         volatility_value_negative=popularity_value

#     try:
#         name= list(opcode_data.keys())[list(opcode_data.values()).index(opcode)]
#         popularity_neg[name]=volatility_value_negative
#         popularity_pos[name]=volatility_value_positive
#     except:
#         pass
# sorted_popularity_poitive = sorted(popularity_pos.items(), key=operator.itemgetter(1))
# sorted_popularity_negative = sorted(popularity_neg.items(), key=operator.itemgetter(1), reverse=True) #"USDCHF",
# checkMoney = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF", "GBPNZD"]
# allMoney = []
# for el in sorted_popularity_poitive:
#     if (el[0] in checkMoney):
        
#         allMoney.append(el[0])
#     if len(allMoney) > 3:
#         break
# for el in sorted_popularity_negative:
#     if (el[0] in checkMoney):
#         allMoney.append(el[0])
#     if len(allMoney) > 3:
#         break

print(int(datetime.datetime.now().hour))