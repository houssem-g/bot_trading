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
# https://stackabuse.com/parallel-processing-in-python/

   

        
class multi_trade(threading.Thread):
    def __init__(self, account, monnaie, action, list_id, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.monnaie=monnaie
        self.list_id = list_id
        self.account = account
        self.action = "sell" if action == "put" else action
        print(self.action)
    def run(self):
        # print("start step open a new trade")
        I_want_money=self.account
        self.lock.acquire()
        I_want_money.change_balance("PRACTICE")
        getLeverage = I_want_money.get_available_leverages("crypto", self.monnaie)
        
        multiple=getLeverage[1]["leverages"][0]["regulated_default"]

        instrument_type="crypto"
        instrument_id=self.monnaie
        side=self.action
        amount=100
        leverage=multiple
        type="market"
        limit_price=None 
        stop_price=None 
        stop_lose_kind="percent" 
        stop_lose_value=100
        take_profit_kind="percent" 
        take_profit_value=100 
        use_trail_stop=True 
        auto_margin_call=False 
        use_token_for_commission=False 
        check,id=I_want_money.buy_order(instrument_type=instrument_type, instrument_id=instrument_id,
                    side=side, amount=amount,leverage=leverage,
                    type=type,limit_price=limit_price, stop_price=stop_price,
                    stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
                    take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
                    use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
                    use_token_for_commission=use_token_for_commission)
        self.lock.release()
        self.list_id.append(id)
        return self.list_id
        # time.sleep(3)

        # print(self.action)
        # instrument_type="crypto"
        # instrument_id=self.monnaie
        # side=self.action
        # amount=100
        # leverage=multiple
        # type="market"
        # limit_price=None 
        # stop_price=None 
        # stop_lose_kind="percent" 
        # stop_lose_value=95 
        # take_profit_kind=None 
        # take_profit_value=None 
        # use_trail_stop=True 
        # auto_margin_call=False 
        # use_token_for_commission=False 
        # check,id=I_want_money.buy_order(instrument_type=instrument_type, instrument_id=instrument_id,
        #             side=side, amount=amount,leverage=leverage,
        #             type=type,limit_price=limit_price, stop_price=stop_price,
        #             stop_lose_value=stop_lose_value, stop_lose_kind=stop_lose_kind,
        #             take_profit_value=take_profit_value, take_profit_kind=take_profit_kind,
        #             use_trail_stop=use_trail_stop, auto_margin_call=auto_margin_call,
        #             use_token_for_commission=use_token_for_commission)
        # self.list_id.append(id)
        # return self.list_id
        # time.sleep(3)

class getDataFromIQ(threading.Thread):
    def __init__(self,account,monnaie, lock, listOutput):
        threading.Thread.__init__(self)
        self.monnaie=monnaie
        self.account = account
        self.listOutput = listOutput
        self.lock = lock
    def run(self):
        self.lock.acquire()
        temporaryList = []
        # print("start step get data from IQ")
        end_from_time = time.time()
        I_want_money=self.account
        data= I_want_money.get_candles(self.monnaie, 1800, 70, end_from_time)
        self.lock.release()
        temporaryList.append(data)
        temporaryList.append(self.monnaie)
        self.listOutput.append(temporaryList)
        
        



def indicator_processing(data):
    monIndic = {"action":"", "date":""}
    monIndic["monnaie"] = data[1]
    data = pd.DataFrame(data[0])
    classeAllIndic = myModule.get_all_indicator(data, monIndic)

    monIndic = classeAllIndic.check_indicateurs()
    return monIndic


class MyBot():
    indicator_processing = staticmethod(indicator_processing)
    def __init__(self, account, login, pwd, lastPairGagnante):
        self.account = account
        self.login = login
        self.pwd = pwd
        self.lastPairGagnante = lastPairGagnante
    
    def loopPrediction(self):

        I_want_money = self.account
        opcode_data=I_want_money.get_all_ACTIVES_OPCODE()

        instrument_type="crypto"#"binary-option"/"digital-option"/"forex"/"cfd"/"crypto"
        I_want_money.subscribe_top_assets_updated(instrument_type)


        while True:
                if I_want_money.get_top_assets_updated(instrument_type)!=None:
                        break

        top_assets=I_want_money.get_top_assets_updated(instrument_type)

        popularity_pos={}
        allCurrencies = I_want_money.get_all_ACTIVES_OPCODE()
        # print(allCurrencies)
        for asset in top_assets:
                opcode=asset["active_id"]
                # if (asset["expiration"]["is_valid"] == True):
                popularity_value=asset["volatility"]["value"]
                volatility_value_positive=popularity_value
                try:
                        name= list(opcode_data.keys())[list(opcode_data.values()).index(opcode)]
                        popularity_pos[name]=volatility_value_positive
                except:
                        pass
        sorted_popularity_positive = sorted(popularity_pos.items(), key=operator.itemgetter(1), reverse=True)

        allMoney = []
        # print(sorted_popularity_positive)
        for el in sorted_popularity_positive:
                # if (el[0] in checkMoney):
                
                allMoney.append(el[0])
                if len(allMoney) > 1:
                        break
        # allMoney = ["EURUSD-OTC"]
        print(allMoney)
        listOutput = []
        listProcess= []     
        pool = Pool(processes=2)
        listProcessrades = []
        list_id = []
        lock=threading.Lock()

        resAction = ["put", "buy"]
        for i, monnaie in enumerate(allMoney):
            proc = "process" + str(i)
            listProcessrades.append(proc)
            globals()[proc] = multi_trade(I_want_money, monnaie, resAction[i], list_id, lock)
        for el in listProcessrades:
            eval(el).start()
        for el in listProcessrades:
            eval(el).join()
                       
        now = 1800-datetime.datetime.now().second
        print("Apres le travail le repos, je vais dormir ", now, " seconds a plus !")
        time.sleep(now)
            
    
if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login, credentials.mdp2)
    iq.connect()
    print("connexion succed hamdoullah !")
    print("allahouma tawakalna aalaik !")
    lastPairGagnante = {"IOTUSD": {"action":"", "temps" : datetime.datetime.now()}, "ADAUSD": {"action":"", "temps" : datetime.datetime.now()}, 
                        "BTCUSD": {"action":"", "temps" : datetime.datetime.now()}, "ETHUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "LTCUSD": {"action":"", "temps" : datetime.datetime.now()}, "XLMUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "BTGUSD": {"action":"", "temps" : datetime.datetime.now()}, "QTMUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "OMGUSD": {"action":"", "temps" : datetime.datetime.now()}, "XRPUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "TRXUSD": {"action":"", "temps" : datetime.datetime.now()}, "EOSUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "ZECUSD": {"action":"", "temps" : datetime.datetime.now()}, "ETCUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "DSHUSD": {"action":"", "temps" : datetime.datetime.now()}, "BNBUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "ONTUSD": {"action":"", "temps" : datetime.datetime.now()}, "NEOUSD": {"action":"", "temps" : datetime.datetime.now()}}
    # lastPairGagnante = {"EURUSD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "USDCHF-OTC": {"action":"", "temps" : datetime.datetime.now()}}
    getMethod= MyBot(iq, "*********@gmail.com","******", lastPairGagnante)
    enterTrade = True
    # getMethod.loopPrediction() 
    while enterTrade == True:
        getMethod.loopPrediction() 

                
# ["IOTUSD", "ADAUSD", "BTCUSD", "ETHUSD", "LTCUSD", "XLMUSD", "BTGUSD", "QTMUSD", "OMGUSD", "XRPUSD", "TRXUSD", "EOSUSD", "ZECUSD", "ETCUSD",
# "DSHUSD", "BNBUSD",  "ONTUSD", "NEOUSD"]