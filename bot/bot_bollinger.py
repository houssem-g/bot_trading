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
        
        I_want_money = self.account
        # getPosition = I_want_money.get_digital_position(self.id)
        # currentTrade=getPosition['msg']
        # print(type(self.id))
        currentTrade = "open"
        while currentTrade == "open":
            # print(isinstance(self.id, int))
            # if (self.id.is_integer()):
            PL= I_want_money.get_digital_spot_profit_after_sale(self.id)
           
            if PL!=None and PL > 10 :
                I_want_money.close_digital_option(self.id)
                currentTrade = "close"
                print("percentage gain : ", PL)
            elif PL!=None and self.id!= None and PL < -51: #and time.time() - startTrade > 200:
                I_want_money.close_digital_option(self.id)
                currentTrade = "close"
            # if(I_want_money.get_digital_position(self.id)['msg'] is not None):
            #     currentTrade=I_want_money.get_digital_position(self.id)['msg']['position']['status']
        
class multi_trade(threading.Thread):
    def __init__(self, account, monnaie, list_id, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.monnaie=monnaie
        self.list_id = list_id
        self.account = account
    def run(self):
        I_want_money=self.account
        price = 100
        action = "put"
        duration = 15
        self.lock.acquire()
        I_want_money.subscribe_strike_list(self.monnaie,duration)
        _,id = I_want_money.buy_digital_spot(self.monnaie,price,action,duration)
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
        end_from_time = time.time()
        I_want_money=self.account
        data= I_want_money.get_candles(self.monnaie, 60, 20, end_from_time)
        self.listOutput.append(tuple((data, self.monnaie)),)





def indicator_processing(data, monnaie):
    outputBolliger = ""
    close = []
    for el in data:
        close.append(el['close'])
    df=pd.DataFrame(close, columns=['close']) 
    rsi = ta.momentum.rsi(df['close'], 14)
    bandBol = ta.volatility.BollingerBands(df['close'], 14, 2)
    indicatorSupBandDol = bandBol.bollinger_hband_indicator()
    print(rsi[19],"test rsi and bollinger pour",monnaie, " ", indicatorSupBandDol[19])

    if ((indicatorSupBandDol[19] > 0 or indicatorSupBandDol[18] > 0) and rsi[19]> 81):
        outputBolliger = monnaie
        return outputBolliger


class MyBot():
    indicator_processing = staticmethod(indicator_processing)
    def __init__(self, account, login, pwd, lastPairGagnante):
        self.account = account
        self.login = login
        self.pwd = pwd
        self.lastPairGagnante = lastPairGagnante
    
    def loopPrediction(self):
        end_from_time=time.time()
        allMoney = ["EURUSD", "GBPJPY", "USDCHF", "GBPUSD", "EURGBP", "AUDCAD", "AUDUSD"]
        bollinger = ""
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
        # print(pool_output)
        resMonnaie = []
        for el in pool_output:
            if el != None:
                resMonnaie.append(el)
        listProcessrades = []
        list_id = []
        lock=threading.Lock()
        if len(resMonnaie)>0:
            for i, monnaie in enumerate(resMonnaie):
                proc = "process" + str(i)
                listProcessrades.append(proc)
                globals()[proc] = multi_trade(I_want_money, monnaie, list_id, lock)
            for el in listProcessrades:
                eval(el).start()
            for el in listProcessrades:
                eval(el).join()
        # print("this is list of id ", list_id)
        listProcessrades = []
        
        for i, id in enumerate(list_id):
            proc = "process" + str(i)
            listProcessrades.append(proc)
            globals()[proc] = check_trade(I_want_money, id)
        for el in listProcessrades:
            eval(el).start()
        for el in listProcessrades:
            eval(el).join()

if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login, credentials.mdp2)
    iq.connect()


    getMethod= MyBot(iq, credentials.login, credentials.mdp2, "")
    enterTrade = True
    while enterTrade == True:
        getMethod.loopPrediction()
