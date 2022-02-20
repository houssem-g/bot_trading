

import trendln
from tapy import Indicators

import talib
from pyiqoptionapi import *
import sys
# from talipp.indicators import RSI
import datetime
import time
import ta
from talipp.indicators import EMA, SMA, RSI
import numpy as np
import pandas as pd
from .. import credentials
from iqoptionapi.stable_api import IQ_Option


# import tatspy

I_want_money = IQ_Option(credentials.login, credentials.mdp2)
I_want_money.connect()


def computeRSI (data, time_window):
    diff = data.diff(1).dropna()        # diff in one field(one day)

    #this preservers dimensions off diff values
    up_chg = 0 * diff
    down_chg = 0 * diff
    
    # up change is equal to the positive difference, otherwise equal to zero
    up_chg[diff > 0] = diff[ diff>0 ]
    
    # down change is equal to negative deifference, otherwise equal to zero
    down_chg[diff < 0] = diff[ diff < 0 ]
    # check pandas documentation for ewm
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.ewm.html
    # values are related to exponential decay
    # we set com=time_window-1 so we get decay alpha=1/time_window
    up_chg_avg   = up_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    down_chg_avg = down_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
    
    rs = abs(up_chg_avg/down_chg_avg)
    rsi = 100 - 100/(1+rs)
    return rsi


end_from_time = time.time()
data= I_want_money.get_candles("USDJPY", 60, 70, end_from_time)
data = pd.DataFrame(data)
rsi = computeRSI(data['close'], 7)

lastRsi = rsi.iloc[-1]
last2Rsi = rsi.iloc[-2]
tendance = ''
if (lastRsi > last2Rsi):
    tendance = 'up'
elif (lastRsi < last2Rsi):
    tendance = 'down'
print(rsi)
print(tendance)