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
import ind_cci_macd as myModule
from .. import credentials
# https://stackabuse.com/parallel-processing-in-python/

class check_trade(threading.Thread):
    def __init__(self, account, id, lock, checkWin, pool_output, lastPairGagnante):
    # def __init__(self, account, id, lock, checkWin, lastPairGagnante):
        threading.Thread.__init__(self)
        self.id = id
        self.account = account
        self.lock = lock
        self.checkWin = checkWin
        self.event = threading.Event()
        self.lastPairGagnante = lastPairGagnante
        self.pool_output = pool_output
    def stop(self):
        self.event.set()
    def run(self):
        time.sleep(2)
        startTrade = int(datetime.datetime.now().minute)
        print("start step check trade")
        time.sleep(2)
        I_want_money = self.account
        # print(self.pool_output)
        
        
        # currentTrade=getPosition
        print(self.id)
        currentTrade = "open"
        self.lock.acquire()   
        #while I_want_money.get_async_order(self.id)['position-changed']['msg']['status'] =='open':
        while True:
            try:
                 
                PL= I_want_money.get_digital_spot_profit_after_sale(self.id)
                # print(I_want_money.get_digital_spot_profit_after_sale(self.id))
                
            except Exception as e:         
                
                print(e)
                # sys.exit(1)
                now = 65-datetime.datetime.now().second
                if (now > 30):
                    print(" I am gonna sleep 30 seconds")
                    time.sleep(30)
                else:
                    print(" I am gonna sleep ", now, " seconds")
                    time.sleep(now)

                python = sys.executable
                os.execl(python, python, *sys.argv)
                
 

                
            
            check,win=I_want_money.check_win_digital_v2(self.id)
            if check:
                print("check : ", check)
                print("win : ", win)
                # print(self.pool_output)
                currentBalance = I_want_money.get_balance()
                checkWin = 1 if win > 0 else -1
                trade = [{"date" : datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), "nom":credentials.nom, "prenom":credentials.prenom, "login":credentials.login, "balance":currentBalance, "check_win":checkWin}]
                classeTableCheck = myDb.save_to_db(trade, "accounts")
                classeTableCheck.insert_data()
                configTrade = []
                monnaie = I_want_money.get_digital_position(self.id)['msg']['position']["instrument_underlying"]
                for el in self.pool_output:
                    if el["monnaie"] == monnaie:
                        configTrade.append(el)
                        break

                configTrade[0]["gain"] = int(win)
                configTrade[0]["check_win"] = checkWin
                classeTableCheck = myDb.save_to_db(configTrade, "tab_check")
                classeTableCheck.insert_data()
                break
     

        self.lock.release()   
        

        sys.exit()      

        
class multi_trade(threading.Thread):
    def __init__(self, account, monnaie, action, list_id, lock):
        threading.Thread.__init__(self)
        self.lock = lock
        self.monnaie=monnaie
        self.list_id = list_id
        self.account = account
        self.action = action
        print(self.action)
    def run(self):
        print("start step open a new trade")
        I_want_money=self.account
        price = 6 
        duration = 5
        self.lock.acquire()
        #MODE: "PRACTICE"/"REAL"
        I_want_money.change_balance("PRACTICE")
        I_want_money.subscribe_strike_list(self.monnaie,duration)
        _,id = I_want_money.buy_digital_spot(self.monnaie,price,self.action,duration)
        try:
            # time.sleep(2)
            PL= I_want_money.get_digital_spot_profit_after_sale(id)
        except Exception as e:
            print(e)
            print("cette paire, ", self.monnaie," presente un pb")
            self.lock.release()
            # self.run()
            return []
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
        print("start step get data from IQ")
        end_from_time = time.time()
        I_want_money=self.account
        data= I_want_money.get_candles(self.monnaie, 60, 40, end_from_time)
        # data= I_want_money.get_candles(self.monnaie, 60, 60, end_from_time)
        self.lock.release()
        temporaryList.append(data)
        temporaryList.append(self.monnaie)
        self.listOutput.append(temporaryList)
        

def indicator_processing(data):
    monIndic = {"action":"", "date":""}
    monIndic["monnaie"] = data[1]
    data = pd.DataFrame(data[0])
    classeAllIndic = myModule.get_indicator(data, monIndic)
    # monIndic = classeAllIndic.macd_SR_sma_indicator()
    # monIndic = classeAllIndic.ssb_and_oscillator()
    monIndic = classeAllIndic.macd_cci_indicator()
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
        # allMoney = ["EURUSD", "GBPJPY", "USDCHF", "GBPUSD", "EURGBP"]
        # allMoney = ["EURUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY"]
        # allMoney = ["AUDCAD", "AUDUSD", "GBPCAD", "EURAUD", "GBPAUD", "EURCAD", "AUDJPY"]
        # allMoney = ["EURUSD-OTC", "USDCHF-OTC"]
        # bollinger = ""
        I_want_money = self.account

        # allMoney = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF", "GBPNZD"]
        allMoney = ["EURUSD-OTC"]
        # EURAUD et EURCAD on provoqué plus de perte que de gqin donc je les supprimes
        print(allMoney)
        listOutput = []
        listProcess= []
        lock=threading.Lock()
        # getDataFromIQ= getDataFromIQ(I_want_money, "","", )
        for i, monnaie in enumerate(allMoney):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = getDataFromIQ(I_want_money, monnaie, lock, listOutput)
        for el in listProcess:
            eval(el).start()
        for el in listProcess:
            eval(el).join()
        
        pool = Pool(processes=7)
        # pool = Pool(processes=3)
        # pool_output = [print(el) for el in listOutput]
        pool_output = pool.map(MyBot.indicator_processing, listOutput, chunksize=1)
        pool.close()
        pool.join()
        # roots = [r.get() for r in pool_output]
        # print(pool_output)
        resMonnaie = []
        resAction =[]
        # pool_output = [{'action': 'put', 'monnaie': 'EURUSD-OTC'}]
        for el in pool_output:
            print(el["monnaie"])
            if (el["action"] != "" and
                (lastPairGagnante[el["monnaie"]]["action"] != el["action"] or
                (datetime.datetime.now() - lastPairGagnante[el["monnaie"]]["temps"]).total_seconds() /60 > 8)):
                lastPairGagnante[el["monnaie"]]["action"] = el["action"]
                lastPairGagnante[el["monnaie"]]["temps"] = datetime.datetime.now()
                resMonnaie.append(el["monnaie"])
                resAction.append(el["action"])
        
        # resAction = ['put', 'call', 'call', 'put', 'put']
        # resMonnaie = ['EURUSD', 'GBPJPY', 'USDCHF', 'GBPUSD', 'EURGBP']
        listProcessrades = []
        list_id = []
        lock=threading.Lock()
        # print("resMonnaie :", resMonnaie)
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
            checkWin = []
            if (len(list_id) > 0):
                for i, id in enumerate(list_id):
                    proc = "process" + str(i)
                    listProcessrades.append(proc)
                    globals()[proc] = check_trade(I_want_money, id, lock, checkWin, pool_output, lastPairGagnante)
                    # globals()[proc] = check_trade(I_want_money, id, lock, checkWin, lastPairGagnante)
                for el in listProcessrades:
                    eval(el).start()
                for el in listProcessrades:
                    eval(el).join()
                conn = psycopg2.connect(user=credentials.user,
                                        password=credentials.password,
                                        host=credentials.host,
                                        port=credentials.port,
                                        database=credentials.database)
                today = datetime.date.today()
                lyoum = today.strftime("%Y-%m-%d")
                checkWin = pd.read_sql_query('''
                        select distinct substring(CAST(DATE AS text), 0, 11) as date, sum(check_win) OVER (PARTITION BY substring(CAST(DATE AS text), 0, 11)) as nb
                        from accounts where substring(CAST(DATE AS text), 0, 11) = ''' + "'"+ lyoum + "'"+ ''' 
                        
                        ''', conn)
                print("number of trades : ", checkWin)
                if (checkWin["nb"].iloc[0] > 1 or int(datetime.datetime.now().hour) > 19):
                    print("Fin de journée.")
                    exit()

                
                now = 49-datetime.datetime.now().second
                if (now < 0):
                    now = 1
                print("Apres le travail le repos, je vais dormir ", now, " seconds a plus !")
                time.sleep(now)
            
        else:
            conn = psycopg2.connect(user=credentials.user,
                                    password=credentials.password,
                                    host=credentials.host,
                                    port=credentials.port,
                                    database=credentials.database)
            today = datetime.date.today()
            lyoum = today.strftime("%Y-%m-%d")
            checkWin = pd.read_sql_query('''
                    select distinct substring(CAST(DATE AS text), 0, 11) as date, sum(check_win) OVER (PARTITION BY substring(CAST(DATE AS text), 0, 11)) as nb
                    from accounts where substring(CAST(DATE AS text), 0, 11) = ''' + "'"+ lyoum + "'"+ ''' 
                    
                    ''', conn)
            print("number of trades : ", checkWin)

            if (int(datetime.datetime.now().hour) > 19 or (len(checkWin.index) > 0 and checkWin["nb"].iloc[0] > 1)):
                print("Fin de journée.")
                exit()

            now = 49-datetime.datetime.now().second
            if (now < 0):
                now = 1
            print("hi I am gonna stop for ", now, " seconds !")
            time.sleep(now)








        
if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login, credentials.mdp2)
    iq.connect()
    print("connexion succed hamdoullah !")
    print("allahouma tawakalna aalaik !")
    lastPairGagnante = {"EURUSD": {"action":"", "temps" : datetime.datetime.now()}, "GBPJPY": {"action":"", "temps" : datetime.datetime.now()}, 
                        "USDCHF": {"action":"", "temps" : datetime.datetime.now()}, "EURCHF": {"action":"", "temps" : datetime.datetime.now()},
                        "GBPUSD": {"action":"", "temps" : datetime.datetime.now()}, "EURGBP": {"action":"", "temps" : datetime.datetime.now()},
                        "AUDCAD": {"action":"", "temps" : datetime.datetime.now()}, "AUDUSD": {"action":"", "temps" : datetime.datetime.now()},
                        "EURJPY": {"action":"", "temps" : datetime.datetime.now()}, "GBPCAD": {"action":"", "temps" : datetime.datetime.now()},
                        "EURCAD": {"action":"", "temps" : datetime.datetime.now()}, "EURAUD": {"action":"", "temps" : datetime.datetime.now()},
                        "GBPAUD": {"action":"", "temps" : datetime.datetime.now()}, "AUDJPY": {"action":"", "temps" : datetime.datetime.now()},
                        "USDCAD": {"action":"", "temps" : datetime.datetime.now()}, "EURJPY": {"action":"", "temps" : datetime.datetime.now()},
                        "GBPCHF": {"action":"", "temps" : datetime.datetime.now()}, "GBPNZD": {"action":"", "temps" : datetime.datetime.now()}}
    # lastPairGagnante = {"EURUSD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "USDCHF-OTC": {"action":"", "temps" : datetime.datetime.now()}}
    getMethod= MyBot(iq, credentials.login, credentials.mdp2, lastPairGagnante)
    enterTrade = True
    # getMethod.loopPrediction()
    while enterTrade == True:
        getMethod.loopPrediction() 
  