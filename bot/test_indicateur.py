import threading
from tradingview_ta import TA_Handler, Interval, Exchange
import json
from talib.abstract import *
from pyiqoptionapi import *
from datetime import datetime
import time
import ta
import numpy as np
import pandas as pd
import psycopg2
from iqoptionapi.stable_api import IQ_Option
from multiprocessing import Process, Queue, Pool, Manager
from itertools import product
import threading
from .. import credentials
class check_trade(threading.Thread):
    def __init__(self, account, id):
        threading.Thread.__init__(self)
        self.id = id
        self.account = account
    
    def run(self):
        print("start step check trade")
        time.sleep(2)
        I_want_money = self.account
        
        # getPosition = I_want_money.get_digital_position(self.id)
        # currentTrade=getPosition['msg']
        # print(type(self.id))
        # currentTrade = "open"
        # while currentTrade == "open":
        while I_want_money.get_async_order(self.id)['position-changed']['msg']['status'] == 'open':
            PL= I_want_money.get_digital_spot_profit_after_sale(self.id)
            if PL!=None and PL > 10 :
                I_want_money.close_digital_option(self.id)
                print("percentage gain : ", PL)
            elif PL!=None and self.id!= None and PL < -51: #and time.time() - startTrade > 200:
                I_want_money.close_digital_option(self.id)
               

        
class multi_trade(threading.Thread):
    def __init__(self, account, monnaie, action, list_id, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.monnaie=monnaie
        self.list_id = list_id
        self.account = account
        self.action = action
    def run(self):
        print("start step open a new trade")
        I_want_money=self.account
        price = 100
        duration = 15
        self.lock.acquire()
        I_want_money.subscribe_strike_list(self.monnaie,duration)
        _,id = I_want_money.buy_digital_spot(self.monnaie,price,self.action,duration)
        self.lock.release()
        self.list_id.append(id)
        return self.list_id
        # time.sleep(3)


class getDataFromIQ(threading.Thread):
    def __init__(self,account,monnaie, listOutput):
        threading.Thread.__init__(self)
        self.monnaie=monnaie
        self.account = account
        self.listOutput = listOutput
    def run(self):
        print("start step get data from IQ")
        end_from_time = time.time()
        I_want_money=self.account
        data= I_want_money.get_candles(self.monnaie, 60, 52, end_from_time)
        self.listOutput.append(tuple((data, self.monnaie)),)





def indicator_processing(data, monnaie):
    # condition_buy_1 = (
    #                     df["crossingTenkanKijun"][ind] <0 and
    #                     df["crossingTenkanKijun"][ind-1] > 0 and
    #                     df["kujin"].iloc[-1] < df["SSA"].iloc[-1] and
    #                     df["tenkan"].iloc[-1] < df["SSB"].iloc[-1] and 
    #                     df["close"].iloc[-26] < df["SSA"].iloc[-26] and
    #                     df["close"].iloc[-26] < df["SSB"].iloc[-26]   
    #                 )
    column_names = ["SSA", "SSB", "tendanceCloudDf", "kujin", "tenkan", "close", "crossingTenkanKijun"]
    df = pd.DataFrame(columns = column_names)
    monIndic = {"crossing":[], "action":"", "strategie1":"", "strategie2":""}
    monIndic["monnaie"] = monnaie
    data = pd.DataFrame(data)
    indicateur = ta.trend.IchimokuIndicator(data['max'], data['min'], 9, 26, 52)
    indicateurSSB = indicateur.ichimoku_b()
    indicateurSSA = indicateur.ichimoku_a()
    indicateurKujin = indicateur.ichimoku_base_line()
    indcateurTenkan = indicateur.ichimoku_conversion_line()
    df["SSA"] = indicateurSSA
    df["SSB"] = indicateurSSB
    df["kujin"] = indicateurKujin
    df["tenkan"] = indcateurTenkan
    df["tendanceCloudDf"] = df["SSA"].iloc[-10:] - df["SSB"].iloc[-10:]
    df["crossingTenkanKijun"] = df["kujin"].iloc[-14:] - df["tenkan"].iloc[-14:]
    df["close"] = data["close"]
    df["open"] = data["open"]
    for ind in df.iloc[-10:].index:
        # if(df["crossingTenkanKijun"][ind] <0 and df["crossingTenkanKijun"][ind-1] > 0 ):
        #     monIndic["crossing"].append(52 - ind)
        # elif(df["crossingTenkanKijun"][ind] >0 and df["crossingTenkanKijun"][ind-1] < 0 ):
        #     monIndic["crossing"].append(52 - ind)
        if (df["crossingTenkanKijun"][ind] <0 and df["crossingTenkanKijun"][ind-1] > 0) :
            monIndic["crossing"].append(52 - ind)

            # df["kujin"].iloc[-1] < df["SSA"].iloc[-1] and
            # df["tenkan"].iloc[-1] < df["SSB"].iloc[-1]

    minCloud = min(df["SSA"][ind], df["SSB"][ind])
    maxCloud = max(df["SSA"][ind], df["SSB"][ind]) 
    if (df["close"].iloc[-2] > minCloud and df["close"].iloc[-2] < maxCloud):
        monIndic["previousBougie"] = "inside"
    else:
        monIndic["previousBougie"] = "outside"

    if (df["tendanceCloudDf"].iloc[-1] < 0) :
        monIndic["cloud"] = "low"
    else :
        monIndic["cloud"] = "high"
    
    if (df["open"].iloc[-1] > df["SSA"].iloc[-1] and df["open"].iloc[-1] > df["SSB"].iloc[-1] and monIndic["previousBougie"] == "inside"):
        monIndic["action"] = "call"
    elif (df["open"].iloc[-1] < df["SSA"].iloc[-1] and df["open"].iloc[-1] < df["SSB"].iloc[-1] and monIndic["previousBougie"] == "inside"):
        monIndic["action"] = "put"
    return monIndic


class MyBot():
    indicator_processing = staticmethod(indicator_processing)
    def __init__(self, account, login, pwd, lastPairGagnante):
        self.account = account
        self.login = login
        self.pwd = pwd
        self.lastPairGagnante = lastPairGagnante
    
    def loopPrediction(self):
        # end_from_time=time.time()
        # allMoney = ["EURUSD", "GBPJPY", "USDCHF", "GBPUSD", "EURGBP", "AUDCAD", "AUDUSD"]
        allMoney = ["EURUSD-OTC", "USDCHF-OTC", "GBPUSD-OTC", "EURGBP-OTC"]
        # bollinger = ""
        I_want_money = self.account
        listOutput = []
        listProcess= []
        # getDataFromIQ= getDataFromIQ(I_want_money, "","", )
        for i, monnaie in enumerate(allMoney):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = getDataFromIQ(I_want_money, monnaie, listOutput)
        for el in listProcess:
            eval(el).start()
        for el in listProcess:
            eval(el).join()

        t = Pool(processes = 3)
        pool_output = t.starmap(MyBot.indicator_processing, listOutput)
        t.close()
        t.join()
        print(pool_output)
        resMonnaie = []
        resAction =[]
        for el in pool_output:
            if len(el["crossing"]) > 0 and el["previousBougie"] == "inside" and el["action"] != "":
                resMonnaie.append(el["monnaie"])
                resAction.append(el["action"])
        listProcessrades = []
        list_id = []
        lock=threading.Lock()
        print("resMonnaie :", resMonnaie)
        if len(resMonnaie)>0:
            for i, monnaie in enumerate(resMonnaie):
                proc = "process" + str(i)
                listProcessrades.append(proc)
                globals()[proc] = multi_trade(I_want_money, monnaie, resAction[i], list_id, lock)
            for el in listProcessrades:
                eval(el).start()
            for el in listProcessrades:
                eval(el).join()
       

        listProcessrades = []
        
        for i, id in enumerate(list_id):
            proc = "process" + str(i)
            listProcessrades.append(proc)
            globals()[proc] = check_trade(I_want_money, id)
        for el in listProcessrades:
            eval(el).start()
        for el in listProcessrades:
            eval(el).join()
        time.sleep(55)
if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login, credentials.mdp2)
    iq.connect()
    print("connexion succed !")


    getMethod= MyBot(iq, credentials.login,credentials.mdp2, "")
    enterTrade = True
    while enterTrade == True:
        getMethod.loopPrediction()
