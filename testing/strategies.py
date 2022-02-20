import psycopg2
import pandas as pd
import threading
import credentials
from os import getpid
class Strategy():
    def __init__(self, data):
        self.data = data


    def get_time(self, tps):
        if (tps >= 55 and tps < 60):
            return 60
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

    def stZaineb(self):
        # lock=threading.Lock()
        # print("I'm process", getpid())
        data = self.data
        # print("monnaie : ", data)
        monIndic = {}
        monIndic["action"] = ""
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        
        currentDate = "%" + data["to"].iloc[-1] +  "%"
        previousDate = "%" + data["to"].iloc[-2] +  "%"
        previous2Date = "%" + data["to"].iloc[-3] +  "%"
        # ne pas oublier de remettre figures à la place de figures_crypto 
        data_buy = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bullish_engulfing = 'True' or
                                piercing_pattern = 'True' or
                                inverted_hammer = 'True' or
                                hammer = 'True' or
                                morning_star = 'True'
                                ) and (
                                CAST(time_fin AS text) LIKE ''' + " '"+previous2Date +"'" + ''' or
                                CAST(time_fin AS text) LIKE '''+ " '"+previousDate + "'"+ '''  )
                                and monnaie = '''+ "'"+data['monnaie'].iloc[-1] + "'"+'''
                                ''', conn)
        # ne pas oublier de remettre figures à la place de figures_crypto 
        data_put = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bearish_engulfing = 'True' or
                                
                                hanging_man = 'True' or
                                shooting_star = 'True' or
                                evening_star = 'True'
                                ) and (
                                CAST(time_fin AS text) LIKE ''' + " '"+previous2Date +"'" + ''' or
                                CAST(time_fin AS text) LIKE '''+ " '"+previousDate + "'"+ '''  )
                                and monnaie = '''+ "'"+data['monnaie'].iloc[-1]+ "'"+'''
                                
                                ''', conn)
        # conn.close()
        # lock.acquire()
        nowMinutes = str(data["from"].iloc[-1])[-2:]
        timeMaxToTrade = self.get_time(int(nowMinutes)) - int(nowMinutes)
        # print(self.get_time(int(nowMinutes)), " / ", nowMinutes, " / ", timeMaxToTrade)
        
        if (data_buy.shape[0] > 0 and data_put.shape[0] == 0  ):
            monIndic["action"] = "call"
            monIndic["date"] = data["from"].iloc[-1]
            monIndic["delta"] = timeMaxToTrade

        elif (data_buy.shape[0] > 0 and data_buy.shape[0] > data_put.shape[0]):
            monIndic["action"] = "call"
            monIndic["date"] = data["from"].iloc[-1]
            monIndic["delta"] = timeMaxToTrade

        elif (data_put.shape[0] > 0 and data_buy.shape[0] == 0):
            monIndic["action"] = "put"
            monIndic["date"] = data["from"].iloc[-1]
            monIndic["delta"] = timeMaxToTrade

        elif (data_put.shape[0] > 0 and data_put.shape[0] > data_buy.shape[0]):
            monIndic["action"] = "put"
            monIndic["date"] = data["from"].iloc[-1]
            monIndic["delta"] = timeMaxToTrade
        
        # monIndic["dateTrade"] = int(timeMaxToTrade)
        return monIndic

