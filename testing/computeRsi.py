import psycopg2
import pandas as pd
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option
import numpy as np
from .. import credentials


def calculRSI (data, time_window):
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
    # print(rsi)
    tendance = ""
    if (rsi[-2] > rsi[-3]):
        tendance = 'up'
    elif (rsi[-2] < rsi[-3]):
        tendance = 'down'
    return {"rsi" : rsi.iloc[-1], "tendance": tendance}


def isSupport(self, df,i):
    support = df['min'][i] < df['min'][i-1]  and df['min'][i] < df['min'][i+1] \
    and df['min'][i+1] < df['min'][i+2] and df['min'][i-1] < df['min'][i-2]

    return support

def isResistance(self, df,i):
    resistance = df['max'][i] > df['max'][i-1]  and df['max'][i] > df['max'][i+1] \
    and df['max'][i+1] > df['max'][i+2] and df['max'][i-1] > df['max'][i-2] 

    return resistance

def isFarFromLevel(self, l, s, levels):
    return np.sum([abs(l-x) < s  for x in levels]) == 0

conn = psycopg2.connect(user=credentials.user,
                        password=credentials.password,
                        host=credentials.host,
                        port=credentials.port,
                        database=credentials.database)

data = pd.read_sql_query('''
                        select distinct  monnaie, substring(cast(time_fin as text), 0, 17) as time_fin, bullish_engulfing, piercing_pattern, inverted_hammer, hammer, morning_star,
                        bearish_engulfing, hanging_man, shooting_star, evening_star, 0.25 as rsi, False as breakSupport, False as breakResistance, '' as tendance
                        from figures where 
                        (bullish_engulfing = 'True' or
                        piercing_pattern = 'True' or
                        inverted_hammer = 'True' or
                        hammer = 'True' or
                        morning_star = 'True' or
                        bearish_engulfing = 'True' or       
                        hanging_man = 'True' or
                        shooting_star = 'True' or
                        evening_star = 'True') 
                        and cast(substring(cast(time_fin as text), 9, 2) as integer) > 02
                        and cast(substring(cast(time_fin as text), 9, 2) as integer) < 15
                        and cast(substring(cast(time_fin as text), 6, 2) as integer) = 05
                        ''', conn)
print(data)
I_want_money = IQ_Option(credentials.login, credentials.mdp2)
I_want_money.connect()
for ind in data.index:
    converted_date = datetime.strptime(data["time_fin"][ind], "%Y-%m-%d %H:%M")
    tps_stamp = datetime.timestamp(converted_date)
    df = I_want_money.get_candles(data["monnaie"][ind], 60, 40, tps_stamp)
    df = pd.DataFrame(df)
    rsi= calculRSI(df["close"], 7)
    data["rsi"][ind] = float(rsi["rsi"])
    data["tendance"][ind] = rsi["tendance"]

    levelSupport = []
    levelResistance = []
    s =  np.mean(df['max'] - df['min'])
    for i in range(2,df.shape[0]-2):
        if isSupport(df,i):
            l = df['min'].iloc[i]

            if isFarFromLevel(l, s, levelSupport):
                levelSupport.append((l))

        elif isResistance(df,i):
            l = df['max'].iloc[i]

            if isFarFromLevel(l, s, levelResistance):
                levelResistance.append((l))

    nearSupport = levelSupport[-1] if len(levelSupport) > 0 else 0
    nearResistance = levelResistance[-1] if len(levelResistance) > 0 else 10000000

    breakSupport = False
    if (data["close"].iloc[-1] < nearSupport or data["close"].iloc[-2] < nearSupport or data["close"].iloc[-3] < nearSupport or data["close"].iloc[-4] < nearSupport):
        data["breakSupport"][ind] = True
    breakResistance = False
    if (data["close"].iloc[-1] > nearResistance or data["close"].iloc[-2] > nearResistance or data["close"].iloc[-3] > nearResistance or data["close"].iloc[-4] > nearResistance):
        breakResistance = True
        data["breakResistance"][ind] = True

print(data)