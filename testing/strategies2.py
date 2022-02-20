import psycopg2
import pandas as pd
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option
import numpy as np
import warnings
from .. import credentials

class Strategy2():
    warnings.filterwarnings("ignore")
    def get_time(self, tps):
        if (tps >= 55 and tps < 60):
            return 60
        elif (tps >=50 and tps < 55):
            return 55
        elif (tps >= 45 and tps < 50):
            return 50
        elif (tps >= 40 and tps < 45):
            return 45
        elif (tps >= 35 and tps < 40):
            return 40
        elif (tps >= 30 and tps < 35):
            return 35
        elif (tps >= 25 and tps < 30):
            return 30
        elif (tps >= 20 and tps < 25):
            return 25
        elif (tps >= 15 and tps < 20):
            return 20
        elif (tps >= 10 and tps < 15):
            return 15
        elif (tps >= 5 and tps < 10):
            return 10

        else :
            return 5

    def calculRSI (self, data, time_window):
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
        if (rsi.iloc[-2] > rsi.iloc[-3]):
            tendance = 'up'
        elif (rsi.iloc[-2] < rsi.iloc[-3]):
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

    def calc(self):
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)

        data = pd.read_sql_query('''
                                select distinct  monnaie, close, substring(cast(time_fin as text), 0, 17) as time_fin, bullish_engulfing, piercing_pattern, inverted_hammer, hammer, morning_star,
                                bearish_engulfing, hanging_man, shooting_star, evening_star, 0.25 as rsi, False as break_support, False as break_resistance, '' as tendance, 0 as cptr_call, 0 as cptr_put,
                                '' as action, '' as out, 0 as delta,
                                
                                cast(substring(cast(time_fin as text), 15, 2) as integer) as minutes, substring(cast(time_fin as text), 9, 2) as days
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
                                --and cast(substring(cast(time_fin as text), 9, 2) as integer) = 03 and monnaie = 'EURUSD'
                                and cast(substring(cast(time_fin as text), 9, 2) as integer) > 02
                                and cast(substring(cast(time_fin as text), 9, 2) as integer) < 15
                                and cast(substring(cast(time_fin as text), 6, 2) as integer) = 05
                                and cast(substring(cast(time_fin as text), 12, 2) as integer) < 20
                                and monnaie in ('GBPCHF', 'EURJPY', 'AUDJPY', 'GBPAUD', 'AUDCAD', 'USDCAD', 'GBPUSD', 
                                                'GBPJPY', 'EURGBP', 'GBPCAD', 'AUDUSD', 'EURAUD', 'EURCAD', 'EURUSD')
                                ''', conn)
        print("data ok") 
        # print(data)
        I_want_money = IQ_Option(credentials.login, credentials.mdp2)
        I_want_money.connect()
        for ind in data.index:
            converted_date = datetime.strptime(data["time_fin"][ind], "%Y-%m-%d %H:%M")
            tps_stamp = datetime.timestamp(converted_date)
            df = I_want_money.get_candles(data["monnaie"][ind], 60, 40, tps_stamp)
            df = pd.DataFrame(df)
            rsi= self.calculRSI(df["close"], 7)
            data["rsi"].iloc[ind] = float(rsi["rsi"])
            data["tendance"].iloc[ind] = rsi["tendance"]

            levelSupport = []
            levelResistance = []
            s =  np.mean(df['max'] - df['min'])
            for i in range(2,df.shape[0]-2):
                if self.isSupport(df,i):
                    l = df['min'].iloc[i]

                    if self.isFarFromLevel(l, s, levelSupport):
                        levelSupport.append((l))

                elif self.isResistance(df,i):
                    l = df['max'].iloc[i]

                    if self.isFarFromLevel(l, s, levelResistance):
                        levelResistance.append((l))

            nearSupport = levelSupport[-1] if len(levelSupport) > 0 else 0
            nearResistance = levelResistance[-1] if len(levelResistance) > 0 else 10000000

            # 

            if (data["close"].iloc[-1] < nearSupport or data["close"].iloc[-2] < nearSupport or data["close"].iloc[-3] < nearSupport or data["close"].iloc[-4] < nearSupport):
                data["break_support"].iloc[ind] = True
            
            if (data["close"].iloc[-1] > nearResistance or data["close"].iloc[-2] > nearResistance or data["close"].iloc[-3] > nearResistance or data["close"].iloc[-4] > nearResistance):
                data["break_resistance"].iloc[ind] = True


        print("rsi and resistance ok") 
        columns_call = ["bullish_engulfing", "piercing_pattern", "inverted_hammer", "hammer", "morning_star"]
        columns_put = ["bearish_engulfing", "hanging_man", "shooting_star", "evening_star"]
        for ind in data.index:
            cptr_call = 0
            cptr_put = 0
            for el_call in columns_call:
                if(data[el_call].iloc[ind] == 'True'):
                    cptr_call += 1
            data["cptr_call"].iloc[ind] = cptr_call

            for el_put in columns_put:
                if(data[el_put].iloc[ind] == 'True'):
                    cptr_put += 1
            data["cptr_put"].iloc[ind] = cptr_put

        print("start last check")
        for i in range(3, data.shape[0]):
            if (data["cptr_call"].iloc[i] > data["cptr_put"].iloc[i] and data["tendance"].iloc[i] == 'up' and data["rsi"].iloc[i]  < 38 and (data["break_support"].iloc[i] == True or data["break_resistance"].iloc[i] == True)):
                # if (diffEma[0] < 0 and diffEma[-1] > 0):
                data["action"].iloc[i] = "call"
                timeMaxToTrade = self.get_time(data["minutes"].iloc[i]) - data["minutes"].iloc[i]
                data["delta"].iloc[i] = timeMaxToTrade
            elif (data["cptr_call"].iloc[i] < data["cptr_put"].iloc[i] and data["tendance"].iloc[i] == 'down' and data["rsi"].iloc[i]  < 65 and (data["break_support"].iloc[i] == True or data["break_resistance"].iloc[i] == True)):
                data["action"].iloc[i] = "put"
                timeMaxToTrade = self.get_time(data["minutes"].iloc[i]) - data["minutes"].iloc[i]
                data["delta"].iloc[i] = timeMaxToTrade
        # print(data)
        return data


# getStrat = Strategy2()
# outputStrategies = getStrat.calc()