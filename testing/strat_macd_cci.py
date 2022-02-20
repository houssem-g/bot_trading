import ta
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import trendln
from talipp.indicators import EMA, SMA, RSI
from tapy import Indicators
import psycopg2

class get_indicator():
    '''
    This class has been developed to contain all the indicators
    Args:
    data(pandas.Series): dataframe.
    monIndic(dict): it containing action and monnaie.

    return:
        monIndic (dict) : {"monnaie" : "self.monnaie", "action": "call or put or empty"}
        action is gonna containing a call, a put or an empty string  
    '''
    def __init__(self, data):
        self.data = data
        # self.monIndic = monIndic
        print("***************************************************************************************************")

    def get_time(self, tps):
        if (tps >= 55 and tps < 60):
            return 0
        elif (tps >= 50 and tps < 55):
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
        elif (tps >= 00 and tps < 5):
            return 5


    def loopOverDf(self, pas, df, colCCI, colMACD, colOut):
        for i in range(1, df["close"].shape[0], pas):
            # print(df[colCCI].iloc[i])
            # print(df[colMACD].iloc[i])
            
            if(df[colCCI].iloc[i] < -100 and df[colCCI].iloc[i-1] > -100 and df[colMACD].iloc[i] < 0):
                df[colOut].iloc[i] = "put"
                
            elif(df[colCCI].iloc[i] > 100 and df[colCCI].iloc[i-1] < 100 and df[colMACD].iloc[i] > 0 ):
                df[colOut].iloc[i] = "call"
                
            else:
                df[colOut].iloc[i] = "neutre" 
                
        return df[colOut]


    def macd_cci_indicator(self):
        # print(self.data)
       
        listOutput = []
        column_names = ["monnaie", "from", "open", "close", "high", "low", "cci", "MACD_diff", "line", "signal", "out", "months", "days", "minutes", "delta", "fin"]

        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
        df["open"] = self.data["open"]
        df["high"] = self.data["max"]
        df["low"] = self.data["min"]
        df["monnaie"] = self.data["monnaie"]
        df["from"] = self.data["from"]
        df["days"] = self.data["day"]
        df["months"] = self.data["months"]
        df["minutes"] = self.data["minutes"]

        indicateurCCI = ta.trend.CCIIndicator(df["high"], df["low"], df["close"])
        cci = indicateurCCI.cci()
        df["cci"] = cci
        indicateurMACD = ta.trend.MACD(df["close"])
        # MACD_diff = indicateurMACD.macd_diff()
        # line = indicateurMACD.macd()
        signal = indicateurMACD.macd_signal()
        # df["MACD_diff"] = MACD_diff
        # df["line"] = line
        df["signal"] = signal
        
        df["out"] = self.loopOverDf(2, df, "cci", "signal", "out")
        # df=df.loc[(df['out'] == "put") | (df['out'] == "call")]

        print("************************************* STARTING LOOP STRATEGIE *****************************************")
        for i in range(1, df["close"].shape[0]):
            df["delta"].iloc[i] = self.get_time(int(df["minutes"].iloc[i])) - int(df["minutes"].iloc[i])
            if df["delta"].iloc[i] < 0:
                df["delta"].iloc[i] = 0
            timeEndTrade = str(datetime.strptime(df["from"].iloc[i], "%Y-%m-%d %H:%M") + timedelta(minutes=int(df["delta"].iloc[i])))[:-3]
            # print(timeEndTrade)
            df2 = df[df["from"]==timeEndTrade]
            current_monnaie = df["monnaie"].iloc[i]
            df2 = df2[df2["monnaie"]== current_monnaie]
            
            # print("*************************************")
            if (df2.shape[0] > 0):
                price_end = df2["open"].iloc[0]
                if (df["out"].iloc[i] == "put" and price_end < df["open"].iloc[i]):
                    df["fin"].iloc[i] = "win"
                elif (df["out"].iloc[i] == "put" and price_end > df["open"].iloc[i]):
                    df["fin"].iloc[i] = "lose"
                elif (df["out"].iloc[i] == "call" and price_end > df["open"].iloc[i]):
                    df["fin"].iloc[i] = "win"
                elif (df["out"].iloc[i] == "call" and price_end < df["open"].iloc[i]):
                    df["fin"].iloc[i] = "lose"
            else:
                df["fin"].iloc[i] = "neutre"
        # print(df.head(200))
        return df
