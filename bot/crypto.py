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
import indicators_crypto as myModule
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
    def run(self):
        print("start step open a new trade")
        I_want_money=self.account
        self.lock.acquire()
        I_want_money.change_balance("PRACTICE")
        getLeverage = I_want_money.get_available_leverages("crypto", self.monnaie)
        
        multiple=getLeverage[1]["leverages"][0]["regulated_default"]
        print("multiple : ", multiple)
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
        # try:
        #     # time.sleep(2)
        #     PL= I_want_money.get_positions(id)
        # except Exception as e:
        #     print(e)
        #     print("cette paire, ", self.monnaie," presente un pb")
        #     self.lock.release()
        #     # self.run()
        #     return []
        self.lock.release()
        self.list_id.append(id)
        return self.list_id
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
       
        data= I_want_money.get_candles(self.monnaie, 900, 70, end_from_time)
        self.lock.release()
        temporaryList.append(data)
        temporaryList.append(self.monnaie)
        self.listOutput.append(temporaryList)
        
        



def indicator_processing(data):
    monIndic = {"action":"", "date":""}
    monIndic["monnaie"] = data[1]
    data = pd.DataFrame(data[0])
    # print(data)
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
        # opcode_data=I_want_money.get_all_ACTIVES_OPCODE()

        # instrument_type="crypto"#"binary-option"/"digital-option"/"forex"/"cfd"/"crypto"
        # I_want_money.subscribe_top_assets_updated(instrument_type)


        # while True:
        #         if I_want_money.get_top_assets_updated(instrument_type)!=None:
        #                 break

        # top_assets=I_want_money.get_top_assets_updated(instrument_type)

        # popularity_pos={}
        # allCurrencies = I_want_money.get_all_ACTIVES_OPCODE()
        # # print(allCurrencies)
        # for asset in top_assets:
        #         opcode=asset["active_id"]
        #         # if (asset["expiration"]["is_valid"] == True):
        #         popularity_value=asset["volatility"]["value"]
        #         volatility_value_positive=popularity_value
        #         try:
        #                 name= list(opcode_data.keys())[list(opcode_data.values()).index(opcode)]
        #                 popularity_pos[name]=volatility_value_positive
        #         except:
        #                 pass
        # sorted_popularity_positive = sorted(popularity_pos.items(), key=operator.itemgetter(1), reverse=True)

        # allMoney = []
        # # print(sorted_popularity_positive)
        # for el in sorted_popularity_positive:
        #         # if (el[0] in checkMoney):
                
        #         allMoney.append(el[0])
        #         if len(allMoney) > 15:
        #                 break
        allMoney = ["BTCUSD","ETHUSD", "LTCUSD", "XLMUSD", "BTGUSD", "QTMUSD", "OMGUSD","XRPUSD",
                    "TRXUSD", "EOSUSD", "ZECUSD", "ETCUSD", "DSHUSD"]

        # ["IOTUSD", "ADAUSD", "BTCUSD", "ETHUSD", "LTCUSD", "XLMUSD", "BTGUSD", "QTMUSD", "OMGUSD", "XRPUSD", "TRXUSD", "EOSUSD", "ZECUSD", "ETCUSD",
        #             "DSHUSD", "BNBUSD",  "ONTUSD", "NEOUSD"]
        print(allMoney)
        listOutput = []
        listProcess= []
        lock=threading.Lock()
        
        for i, monnaie in enumerate(allMoney):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = getDataFromIQ(I_want_money, monnaie, lock, listOutput)
        for el in listProcess:
            eval(el).start()
        for el in listProcess:
            eval(el).join()
        
        pool = Pool(processes=7)
      
        
        pool_output = pool.map(MyBot.indicator_processing, listOutput, chunksize=1)
        pool.close()
        pool.join()
        # roots = [r.get() for r in pool_output]
        # print(pool_output)
        resMonnaie = []
        resAction =[]
        # pool_output = [{'action': 'put', 'monnaie': 'EURUSD-OTC'}]
        for el in pool_output:
            if (el["action"] != "" and
                (lastPairGagnante[el["monnaie"]]["action"] != el["action"] or
                (datetime.datetime.now() - lastPairGagnante[el["monnaie"]]["temps"]).total_seconds() /60 > 45)):
                lastPairGagnante[el["monnaie"]]["action"] = el["action"]
                lastPairGagnante[el["monnaie"]]["temps"] = datetime.datetime.now()
                resMonnaie.append(el["monnaie"])
                resAction.append(el["action"])
        

        listProcessrades = []
        list_id = []
        lock=threading.Lock()

        if len(resMonnaie)>0:
            for i, monnaie in enumerate(resMonnaie):
                proc = "process" + str(i)
                listProcessrades.append(proc)
                globals()[proc] = multi_trade(I_want_money, monnaie, resAction[i], list_id, lock)
            for el in listProcessrades:
                eval(el).start()
            for el in listProcessrades:
                eval(el).join()
            currentDate = datetime.datetime.now().minute 
            currentSecondes = datetime.datetime.now().second 

            if (int(currentDate) < 15):
                now = 915 - currentSecondes - (int(currentDate) * 60)
            elif ( 15 <= int(currentDate) < 30):
                now = 1815 - currentSecondes - (int(currentDate) * 60)
            elif ( 30 <= int(currentDate) < 45):
                now = 2715 - currentSecondes - (int(currentDate) * 60)
            elif ( 45 <= int(currentDate)):
                now = 3615 - currentSecondes - (int(currentDate) * 60)
            else : now = 915
            # now = 900-datetime.datetime.now().second
            print("Apres le travail le repos, je vais dormir ", now, " seconds a plus !")
            time.sleep(now)
            
        else:
            currentDate = datetime.datetime.now().minute 
            currentSecondes = datetime.datetime.now().second
            print("***************************************")
            print(currentDate, " / ", currentSecondes)
            if (int(currentDate) < 15):
                now = 915 - currentSecondes - (int(currentDate) * 60)
            elif ( 15 <= int(currentDate) < 30):
                now = 1815 - currentSecondes - (int(currentDate) * 60)
            elif ( 30 <= int(currentDate) < 45):
                now = 2715 - currentSecondes - (int(currentDate) * 60)
            elif ( 45 <= int(currentDate)):
                now = 3615 - currentSecondes - (int(currentDate) * 60)
            else : now = 915
            print("I am gonna stop for ", now, " seconds !")
            time.sleep(now)








        
if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login,credentials.mdp2)
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
    getMethod= MyBot(iq, "hemodisbalkiss@gmail.com","schweppes91", lastPairGagnante)
    enterTrade = True
    # getMethod.loopPrediction() 
    while enterTrade == True:
        getMethod.loopPrediction() 
        # try:
        #     getMethod.loopPrediction()   
        # except Exception as e:
        #     print("un redemarrage complet est nécessaire !")
        #     print(e)
        #     python = sys.executable
        #     os.execl(python, python, *sys.argv)