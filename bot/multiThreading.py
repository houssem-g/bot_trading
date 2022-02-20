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
# manager = Manager()
# listPrice = manager.list()
# listMonnaie = manager.list()
# listAction = manager.list()
# listDuration = manager.list()
from .. import credentials

class check_trade(threading.Thread):
    def __init__(self, account, id):
        threading.Thread.__init__(self)
        self.id = id
        self.account = account
        
    def run(self):
        
        I_want_money = self.account
        getPosition = I_want_money.get_digital_position(self.id)
        currentTrade=getPosition['msg']
        # print(currentTrade)
        while self.id != None:
            PL= I_want_money.get_digital_spot_profit_after_sale(self.id)
            time.sleep(5)
            print("percentage gain : ", PL)
            if PL!=None and PL > 10 :
                I_want_money.close_digital_option(self.id)
                self.id = None
                # print("percentage gain : ", PL)
            elif PL!=None and self.id!= None and PL < -51: #and time.time() - startTrade > 200:
                I_want_money.close_digital_option(self.id)
                self.id = None
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

    # if ((indicatorSupBandDol[19] > 0 or indicatorSupBandDol[18] > 0 or indicatorSupBandDol[17] > 0) and (rsi[19]> 80)):
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
        # allMoney = ["EURUSD", "GBPJPY", "USDCHF", "GBPUSD", "EURGBP", "AUDCAD", "AUDUSD"]
        allMoney = ["EURUSD", "EURJPY"]
        bollinger = ""
        I_want_money = self.account
        listOutput = []
        listProcess= []
        # getDataFromIQ= getDataFromIQ(I_want_money, "","", )
        for i, monnaie in enumerate(allMoney):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = getDataFromIQ(I_want_money, monnaie, listOutput)
            eval(process).start()
        for el in listProcess:
            eval(el).join()

        t = Pool(processes = 3)
        pool_output = t.starmap(MyBot.indicator_processing, listOutput)
        t.close()
        t.join()
        print(pool_output)
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
        print("this is list of id ", list_id)
        listProcessrades = []
        
        for i, id in enumerate(list_id):
            proc = "process" + str(i)
            listProcessrades.append(proc)
            globals()[proc] = check_trade(I_want_money, id)
        for el in listProcessrades:
            eval(el).start()
        for el in listProcessrades:
            eval(el).join()
        time.sleep(5)
if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login, credentials.mdp2)
    iq.connect()


    getMethod= MyBot(iq, credentials.login, credentials.mdp2, "")
    # enterTrade = True
    # while enterTrade == True:
    getMethod.loopPrediction()

# from iqoptionapi.stable_api import IQ_Option 
 
# import threading
  

# class buy_multiThread (threading.Thread):
#     def __init__(self, account,price,ACTIVES,ACTION,expirations):
#         threading.Thread.__init__(self)
#         self.account=account
#         self.price=price
#         self.ACTIVES=ACTIVES
#         self.ACTION=ACTION
#         self.expirations=expirations
#     def run(self):
        # id_list=self.account.buy_multi(self.price, self.ACTIVES, self.ACTION, self.expirations)
#         print(id_list)
 
# account1=IQ_Option(credentials.login, credentials.mdp3)
# account1.connect()
 
# price=[]
# ACTIVES=[]
# ACTION=[]
# expirations=[]
# for i in range(50):
#     price.append(1)
#     ACTIVES.append("EURUSD")
#     ACTION.append("put")
#     expirations.append(1)
# thread1 = buy_multiThread(account1,price, ACTIVES, ACTION,expirations)
# thread2 = buy_multiThread(account1,price, ACTIVES, ACTION,expirations)
# thread1.start() 
# thread2.start()
# thread1.join()
# thread2.join()






                # bollinger = el
                
        # listProcessrades = []
        # if len(res)>0:
        #     print("1111111111111111111111111111111111111111111111111111111111111111111111111111111")
        #     for i, monnaie in enumerate(res):
        #         process = "process" + str(i)
        #         listProcessrades.append(process)
        #         globals()[process] = multi_trade(I_want_money, monnaie)
        #     for el in listProcessrades:
        #         eval(el).start()
        #     for el in listProcessrades:
        #         eval(el).join()

        # bollinger = self.indicator_processing(data, monnaie)
        # if bollinger != "":
        #     break
        # ACTIVES=bollinger
        # duration=15#minute 1 or 5

        # amount = 10

        # action = "put"

        # if bollinger != "" :
        #     I_want_money.subscribe_strike_list(bollinger,duration)
        #     _,id = I_want_money.buy_digital_spot(bollinger,amount,action,duration) 
        #     time.sleep(3)
        #     # getPosition = I_want_money.get_digital_position(id)
        #     # currentTrade=getPosition['msg']['position']['status']
        #     currentTrade = 'open'
        #     while currentTrade == 'open':
        #         PL= I_want_money.get_digital_spot_profit_after_sale(id)
        #         percent = PL/amount * 100
        #         if PL!=None and percent > 10 :
        #             I_want_money.close_digital_option(id)
        #             currentTrade = 'close'
        #             print("percentage gain : ", percent)
        #         elif PL!=None and percent < -51: #and time.time() - startTrade > 200:
        #             I_want_money.close_digital_option(id)
        #             currentTrade = 'close'

        #         if(I_want_money.get_digital_position(id)['msg'] is not None):
        #             currentTrade=I_want_money.get_digital_position(id)['msg']['position']['status']
    
        #     self.lastPairGagnante = bollinger
        #     print("End of trade", bollinger, " / ", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), " / time exec code : ", time.time()- end_from_time)
        # else :
        #     print( "didn't enter in trade  : ", bollinger, "/ ", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "time exec code : ", time.time()- end_from_time, "/ ", time.time(), "/", end_from_time)
            # time.sleep(10)