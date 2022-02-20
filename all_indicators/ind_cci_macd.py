import ta
import pandas as pd
import numpy as np
import datetime
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
    def __init__(self, data, monIndic):
        self.data = data
        self.monIndic = monIndic



    def loopOverDf(self, pas, df, colCCI, colMACD, colOut):
        for i in range(df.shape[0]-1, 30, pas):
            if(df[colCCI][i] < -100 and df[colCCI][i-1] > -100 and df[colMACD][i] < 0):
                df[colOut].iloc[-1] = "put"
                break
            elif(df[colCCI][i] > 100 and df[colCCI][i-1] < 100 and df[colMACD][i] > 0 ):
                df[colOut].iloc[-1] = "call"
                break
            else:
               df[colOut].iloc[-1] = "neutre" 
        return df


    def macd_cci_indicator(self):
        # print(self.data)
        self.monIndic["action"] = ""
        listOutput = []
        column_names = ["close", "high", "low", "cci", "MACD_diff", "line", "signal"]

        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
        df["high"] = self.data["max"]
        df["low"] = self.data["min"]

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
        print(df)
        if (df["cci"].iloc[-1] < -106 and df["cci"].iloc[-2] > -100 and df["signal"].iloc[-1] < 0):
            self.monIndic["action"] = "put"
            self.monIndic["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.monIndic
        elif (df["cci"].iloc[-1] > 106 and df["cci"].iloc[-2] < 100 and df["signal"].iloc[-1] > 0):
            self.monIndic["action"] = "call"
            self.monIndic["date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return self.monIndic
        self.monIndic["action"] = "call"
        return self.monIndic



