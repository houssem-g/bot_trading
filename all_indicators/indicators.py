import ta
import pandas as pd
import numpy as np
import datetime
import trendln
from talipp.indicators import EMA, SMA, RSI
from tapy import Indicators
import psycopg2
import credentials

class get_all_indicator():
    '''
    This class has been developed to contain all the indicators
    Args:
    data(pandas.Series): dataframe.
    monIndic(dict): it containing action and monnaie.

    return:
        monIndic (dict) : {"monnaie" : "self.monnaie", "action": "call or put or empty"}
        action is gonna containing a call, a put or an empty string  
    '''
    def __init__(self, data, monIndic):
        self.data = data
        self.monIndic = monIndic

    def get_time(self, tps):
        if (tps >= 55 and tps < 59):
            return 59
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
    
    def loopOverDf(self, pas, df, col, colOut):
        for i in range(df.shape[0]-1, 30, pas):
            if(df[col][i] > 0 and df[col][i-1] < 0 and df[col][i-2] < 0):
                df[colOut].iloc[-1] = "call"
                break
            elif(df[col][i] < 0 and df[col][i-1] > 0 and df[col][i-2] > 0):
                df[colOut].iloc[-1] = "put"
                break
            else:
               df[colOut].iloc[-1] = "neutre" 
        return df

    def computeRSI (self, data, time_window):
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

  
    
    def request_db(self, monnaie, interval, previousDate):

        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        # cur = datetime.datetime.now().strftime("%Y-%m-%d %H")
        # previousMinutes = str("{0:0>2}".format(datetime.datetime.now().minute - 1))
        # previousDate = "%" + cur + ":" + previousMinutes +  "%"

        df_check_range = pd.read_sql_query('''
                select distinct rsi, o_result_fin, ma_result_fin from prediction where 
                prevision = ''' + "'" + interval + "'" + ''' and
                CAST(res_date AS text) LIKE'''+ "'"+previousDate + "'"+ '''
                and monnaie = '''+ "'"+ monnaie + "'"+'''
                
                ''', conn)
        return df_check_range

    
    def check_indicateurs(self):
     
        self.monIndic["action"] = ""
        levelSupport = []
        levelResistance = []
        s =  np.mean(self.data['max'] - self.data['min'])
        for i in range(2,self.data.shape[0]-2):
            if self.isSupport(self.data,i):
                l = self.data['min'].iloc[i]

                if self.isFarFromLevel(l, s, levelSupport):
                    levelSupport.append((l))

            elif self.isResistance(self.data,i):
                l = self.data['max'].iloc[i]

                if self.isFarFromLevel(l, s, levelResistance):
                    levelResistance.append((l))
        # print(self.monIndic["monnaie"])
        # print(levelSupport)
        # print(levelResistance)
        
        nearSupport = levelSupport[-1] if len(levelSupport) > 0 else 0
        nearResistance = levelResistance[-1] if len(levelResistance) > 0 else 10000000

        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        nowMinutes = str("{0:0>2}".format(datetime.datetime.now().minute))
        now = str("{0:0>2}".format(datetime.datetime.now().minute))
        previousMinutes = str("{0:0>2}".format(datetime.datetime.now().minute - 1))
        previous2Minutes = str("{0:0>2}".format(datetime.datetime.now().minute - 2))
        cur = datetime.datetime.now().strftime("%Y-%m-%d %H")
        currentDate = "%" + cur + ":" + now +  "%"
        previousDate = "%" + cur + ":" + previousMinutes +  "%"
        previous2Date = "%" + cur + ":" + previous2Minutes +  "%"
        # ne pas oublier de remettre figures à la place de figures_crypto 
        data_buy = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bullish_engulfing = 'True' or
                                piercing_pattern = 'True' or
                                inverted_hammer = 'True' or
                                hammer = 'True' or
                                morning_star = 'True'
                                ) and (
                                --CAST(time_fin AS text) LIKE ''' + " '"+currentDate +"'" + ''' or
                                CAST(time_fin AS text) LIKE ''' + " '"+previous2Date +"'" + ''' or
                                CAST(time_fin AS text) LIKE '''+ " '"+previousDate + "'"+ '''  )
                                and monnaie = '''+ "'"+self.monIndic['monnaie'] + "'"+'''
                                

                                ''', conn)
        # ne pas oublier de remettre figures à la place de figures_crypto 
        data_put = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bearish_engulfing = 'True' or
                                
                                hanging_man = 'True' or
                                shooting_star = 'True' or
                                evening_star = 'True'
                                ) and (
                                --CAST(time_fin AS text) LIKE ''' + " '"+currentDate + "'"+ ''' or
                                CAST(time_fin AS text) LIKE ''' + " '"+previous2Date +"'" + ''' or
                                CAST(time_fin AS text) LIKE '''+ " '"+previousDate + "'"+ '''  )
                                and monnaie = '''+ "'"+self.monIndic['monnaie'] + "'"+'''
                                
                                ''', conn)
        conn.close()

        

        column_names = ["close", "max"]
        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
        df["max"] = self.data["max"]
        # df["high"] = self.data["max"][-12:-4]
        # df["low"] = self.data["min"][-12:-4]
        maxpreviousCandle = max(self.data["close"].iloc[-2], self.data["open"].iloc[-2])
        maxprevious2Candle = max(self.data["close"].iloc[-3], self.data["open"].iloc[-3])
        # maxLast10periode = df["high"].max()
        # currenteHigh = df["high"].iloc[-2]
        # idx = df[df["high"]== maxLast10periode].index.values[0]

        breakSupport = False
        if (df["close"].iloc[-1] < nearSupport or df["close"].iloc[-2] < nearSupport or df["close"].iloc[-3] < nearSupport or df["close"].iloc[-4] < nearSupport):
            breakSupport = True
        breakResistance = False
        if (df["close"].iloc[-1] > nearResistance or df["close"].iloc[-2] > nearResistance or df["close"].iloc[-3] > nearResistance or df["close"].iloc[-4] > nearResistance):
            breakResistance = True

        # dfRsi = self.request_db(self.monIndic['monnaie'], '1 MINUTE', prior5minutes)
        rsi = self.computeRSI(self.data["close"], 7)
     
        listBougies = df["close"].values.tolist()
        
        lastRsi = rsi.iloc[-1]
        last2Rsi = rsi.iloc[-2]
        last4Rsi = rsi.iloc[-3]


        tendance = ''
        if ( last2Rsi > last4Rsi):
            tendance = 'up'
        elif ( last2Rsi < last4Rsi ):
            tendance = 'down'
        # rsi = dfRsi["rsi"].iloc[-1]
        timeMaxToTrade = self.get_time(int(nowMinutes)) - int(nowMinutes)

        if(data_buy.shape[0] > 0 or data_put.shape[0] > 0):
            listBougies = df["close"].values.tolist()
            # sma55 = EMA(period = 50, input_values = listBougies)
            # ema25 = EMA(period = 10, input_values = listBougies)
            # listeEma25 = ema25[-9:]
            # listeSma55 = sma55[-9:]
            # diffEma = [listeEma25[i] - listeSma55[i] for i in range(0, 6)]
            print(currentDate)
            print(self.monIndic['monnaie'])
            print(last4Rsi, " / ", last2Rsi, " / ", lastRsi)
            print(tendance)
            print(data_buy.shape[0])
            print(data_put.shape[0])
            # print(diffEma)
            print("levelSupport : ", levelSupport)
            print("levelResistance : ", levelResistance)
            print(breakSupport)
            print(breakResistance)
            print(maxpreviousCandle)
            print(maxprevious2Candle)
        # remmetre and timeMaxToTrade >= 2 pour les trades des fiats and lastRsi < 40 and maxpreviousCandle < maxprevious2Candle
        # and lastRsi > 60 and timeMaxToTrade >= 2 and maxpreviousCandle > maxprevious2Candle 
        
        # if (data_buy.shape[0] > 0 and data_put.shape[0] == 0  and tendance == 'up' and lastRsi < 38 and (breakSupport == True or breakResistance == True)):
        #     # if (diffEma[0] < 0 and diffEma[-1] > 0):
        #     self.monIndic["action"] = "call"
        #     self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        #     print("output : ", self.monIndic)
        #     return self.monIndic
        # elif (data_buy.shape[0] > 0 and data_buy.shape[0] > data_put.shape[0] and tendance == 'up' and lastRsi < 38 and (breakSupport == True or breakResistance == True)):
        #     # if (diffEma[0] < 0 and diffEma[-1] > 0):
        #     self.monIndic["action"] = "call"
        #     self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        #     print("output : ", self.monIndic)
        #     return self.monIndic
        # elif (data_put.shape[0] > 0 and data_buy.shape[0] == 0 and tendance == 'down' and lastRsi > 65 and (breakSupport == True or breakResistance == True)):
        #     # if (diffEma[0] > 0 and diffEma[-1] < 0):            
        #     self.monIndic["action"] = "put"
        #     self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        #     print("output : ", self.monIndic)
        #     return self.monIndic
        # elif (data_put.shape[0] > 0 and data_put.shape[0] > data_buy.shape[0] and tendance == 'down' and lastRsi > 65 and (breakSupport == True or breakResistance == True)):
        #     # if (diffEma[0] > 0 and diffEma[0] <0):            
        #     self.monIndic["action"] = "put"
        #     self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        # # and ((45 > lastRsi > 32) or ( 50 < lastRsi < 75))
        #     print("output : ", self.monIndic)
        #     return self.monIndic

        if(len(levelResistance) > 1):
            id1 = df[df["max"] == levelResistance[-1]].index.values[0]
            id2 = df[df["max"] == levelResistance[-2]].index.values[0]
            print(self.monIndic['monnaie'])
            print("levelSupport : ", levelSupport)
            print("levelResistance : ", levelResistance)
            if(id1 > 6 and id2 > 6 and last2Rsi >= 70 and (df["close"].iloc[-1] > nearResistance or df["close"].iloc[-2] > nearResistance)):
                rsi1 = rsi[id1]
                rsi2 = rsi[id2]
                if (levelResistance[-2] < levelResistance[-1] and rsi2 > rsi1 + 1):
                    self.monIndic["action"] = "put"
                    self.monIndic["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print("divergence/convergence sur rsi")
                    return self.monIndic
                elif (levelResistance[-2] > levelResistance[-1] and rsi2 < rsi1 - 1):
                    self.monIndic["action"] = "call"
                    self.monIndic["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print("divergence/convergence sur rsi")
                    return self.monIndic
        print("output : ", self.monIndic)
        return self.monIndic


