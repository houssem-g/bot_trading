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
import logging
from multiprocessing import Process, Queue, Pool, Manager
from itertools import product
import threading
sys.path.append('E:\\users\houssem\\trading_analysis\\all_indicators')
sys.path.append('E:\\users\houssem\\trading_analysis\\database')
# print(sys.path)
import write_to_db as myDb
import indicators as myModule
import ind_cci_macd as myModule2
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
        print("id : ", self.id)
        # currentTrade = "open"
        # self.lock.acquire()
        #while I_want_money.get_async_order(self.id)['position-changed']['msg']['status'] =='open':
        
        # monid = I_want_money.check_win(self.id)
        monnaie = I_want_money.get_optioninfo_v2(10)
        print( "monnaie", monnaie)
        # except Exception as e:
        #     print(e)
        #     python = sys.executable
        #     os.execl(python, python, *sys.argv)
        while True:
            try:
                 
                PL= I_want_money.get_digital_payout(monnaie)
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
                
            # if PL!=None and PL > 99 :
            #     I_want_money.close_digital_option(self.id)
            #     self.checkWin.append(PL)
            #     print("id ID is : ", self.id, " and the profit is : ", PL)
            #     # check,win=I_want_money.check_win_digital_v2(self.id)
            #     break
            # if PL!=None and self.id!= None and PL < -80 and int(datetime.datetime.now().minute) != startTrade : #and time.time() - startTrade > 200:
            #     time.sleep(1)
            #     PL= I_want_money.get_digital_spot_profit_after_sale(self.id)
            #     if PL!=None and self.id!= None and PL < -80:
            #         I_want_money.close_digital_option(self.id)
            #         self.checkWin.append(PL)
            #         print("id ID is : ", self.id, " and the profit is : ", PL)
            #         check,win=I_want_money.check_win_digital_v2(self.id)
                
            check, win=I_want_money.check_win_digital_v2(self.id)
            
            if check:
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
            if (int(datetime.datetime.now().minute) - startTrade > 6):
                break

        self.lock.release()   
        
        # dbList = []
        # for el in self.pool_output:
        #     action = el ["action"]
        #     for sub_el in el["listOutput"]:
        #         if (sub_el["monnaie"] == monnaie):
        #             sub_el["action"] = action
        #             sub_el["gain"] = PL
        #             sub_el["date_fin"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        #             if (PL < 0):
        #                 sub_el["win_or_lose"] = "lose"
        #             else :
        #                 sub_el["win_or_lose"] = "win"
                    
        #             dbList.append(sub_el)
        # classeTableCheck = myDb.save_to_db(dbList, "tab_check")
        # classeTableCheck.insert_data()
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
        price = 100
        expirations_mode = 5
        self.lock.acquire()
        #MODE: "PRACTICE"/"REAL"
        I_want_money.change_balance("PRACTICE")
        # print(I_want_money.subscribe_strike_list(self.monnaie,duration))
        I_want_money.subscribe_strike_list(self.monnaie,expirations_mode)
        _,id = I_want_money.buy(price, self.monnaie,self.action, expirations_mode)
        try:
            # time.sleep(2)
            PL= I_want_money.get_order(id)
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
        # print("start step get data from IQ")
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
    # classeAllIndic = myModule.get_all_indicator(data, monIndic)
    classeAllIndic = myModule2.get_indicator(data, monIndic)
    monIndic = classeAllIndic.macd_cci_indicator()
    # monIndic = classeAllIndic.ssb_and_oscillator()
    # monIndic = classeAllIndic.check_indicateurs()
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
        opcode_data=I_want_money.get_all_ACTIVES_OPCODE()

        instrument_type="digital-option"#"binary-option"/"digital-option"/"forex"/"cfd"/"crypto"
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
            
            popularity_value=asset["diff_1h"]["value"]
            
            volatility_value_positive=popularity_value
            
            try:
                name= list(opcode_data.keys())[list(opcode_data.values()).index(opcode)]
                popularity_pos[name]=volatility_value_positive
            except:
                pass
        sorted_popularity_positive = sorted(popularity_pos.items(), key=operator.itemgetter(1), reverse=True)

        # if (int(datetime.datetime.now().hour) > 11 and int(datetime.datetime.now().hour) < 15):
        # checkMoney = ["AUDUSD", "GBPCAD", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "GBPCHF"]
        # elif (int(datetime.datetime.now().hour) > 18):
        #     checkMoney = [ "GBPCAD", "EURGBP", "GBPJPY", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        # else :
        checkMoney = "EURUSD-OTC"
        # checkMoney = ["EURUSD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
            # allMoney = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        allMoney = []
        for el in sorted_popularity_positive:
            
            if (el[0] in checkMoney and ((el[1]>0 and el[1] < 0.1) or (el[1]<0 and el[1] > -0.1))):
                
                allMoney.append(el[0])
            if len(allMoney) > 4:
                break
        # allMoney = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF", "GBPNZD"]
        allMoney = ["EURUSD-OTC"]#, "EURGBP-OTC", "EURJPY-OTC", "GBPUSD-OTC"]
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
        print(pool_output)
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

              
      
            

                
                now = 52-datetime.datetime.now().second
                if (now < 0):
                    now = 1
                print("Apres le travail le repos, je vais dormir ", now, " seconds a plus !")
                time.sleep(now)

            now = 52-datetime.datetime.now().second
            if (now < 0):
                now = 1
            print("hi I am gonna stop for ", now, " seconds !")
            time.sleep(now)








        
if __name__ == '__main__':  # If it's executed like a script (not imported)
    # logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')
    if (int(datetime.datetime.now().hour) < 9):
        to_sleep = (60 - int(datetime.datetime.now().minute)) * 60
        print(to_sleep)
        time.sleep(to_sleep)
    header={"User-Agent":r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"}
    cookie={"I_want_money":"GOOD"}
    iq = IQ_Option(credentials.login,credentials.mdp)
    iq.set_session(header,cookie)

    iq.connect()#connect to iqoption
    

    print("connexion succed hamdoullah !")
    print("allahouma tawakalna aalaik !")
    # lastPairGagnante = {"EURUSD": {"action":"", "temps" : datetime.datetime.now()}, "GBPJPY": {"action":"", "temps" : datetime.datetime.now()}, 
    #                     "USDCHF": {"action":"", "temps" : datetime.datetime.now()}, "EURCHF": {"action":"", "temps" : datetime.datetime.now()},
    #                     "GBPUSD": {"action":"", "temps" : datetime.datetime.now()}, "EURGBP": {"action":"", "temps" : datetime.datetime.now()},
    #                     "AUDCAD": {"action":"", "temps" : datetime.datetime.now()}, "AUDUSD": {"action":"", "temps" : datetime.datetime.now()},
    #                     "EURJPY": {"action":"", "temps" : datetime.datetime.now()}, "GBPCAD": {"action":"", "temps" : datetime.datetime.now()},
    #                     "EURCAD": {"action":"", "temps" : datetime.datetime.now()}, "EURAUD": {"action":"", "temps" : datetime.datetime.now()},
    #                     "GBPAUD": {"action":"", "temps" : datetime.datetime.now()}, "AUDJPY": {"action":"", "temps" : datetime.datetime.now()},
    #                     "USDCAD": {"action":"", "temps" : datetime.datetime.now()}, "EURJPY": {"action":"", "temps" : datetime.datetime.now()},
    #                     "GBPCHF": {"action":"", "temps" : datetime.datetime.now()}, "GBPNZD": {"action":"", "temps" : datetime.datetime.now()}}
    lastPairGagnante = {"EURUSD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "GBPJPY-OTC": {"action":"", "temps" : datetime.datetime.now()}, 
                    "USDCHF-OTC": {"action":"", "temps" : datetime.datetime.now()}, "EURCHF-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "GBPUSD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "EURGBP-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "AUDCAD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "AUDUSD-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "EURJPY-OTC": {"action":"", "temps" : datetime.datetime.now()}, "GBPCAD-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "EURCAD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "EURAUD-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "GBPAUD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "AUDJPY-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "USDCAD-OTC": {"action":"", "temps" : datetime.datetime.now()}, "EURJPY-OTC": {"action":"", "temps" : datetime.datetime.now()},
                    "GBPCHF-OTC": {"action":"", "temps" : datetime.datetime.now()}, "GBPNZD-OTC": {"action":"", "temps" : datetime.datetime.now()}}
    getMethod= MyBot(iq, credentials.login,credentials.mdp, lastPairGagnante)
    enterTrade = True
    # getMethod.loopPrediction()
    while enterTrade == True:
        getMethod.loopPrediction() 
