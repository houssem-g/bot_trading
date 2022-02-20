import sys
from iqoptionapi.stable_api import IQ_Option
import time
import pandas as pd
from datetime import datetime, timedelta
from multiprocessing import  Pool, Process
import threading
import warnings
from .. import credentials
from pandas.core.indexes.base import Index
sys.path.append('E:\\users\houssem\\trading_analysis\\testing')
sys.path.append('E:\\users\houssem\\trading_analysis\\database')
import strategies2 as strat
import write_to_db as myDb
warnings.filterwarnings("ignore")

# https://www.epochconverter.com/
# coller Epoch timestamp en tant que dernier parametre dans get_candles
class MyBot():
    
    
    def __init__(self, I_want_money):
        self.I_want_money=I_want_money

    def trades(self, data, obj, money):
        data_to_check = data[data["monnaie"] == money]
        for i in range(0, obj.shape[0]):
            # print(obj["monnaie"].iloc[i])
            timeEndTrade = str(datetime.strptime(obj["time_fin"].iloc[i], "%Y-%m-%d %H:%M") + timedelta(minutes=int(obj["delta"].iloc[i])))[:-3]

            if (data_to_check.shape[0] > 0):
                endTrade = data_to_check[data_to_check["from"]==timeEndTrade]["open"].iloc[0]
                # print(money, " : ", i)
                # print(obj["time_fin"])
                # print(obj["time_fin"].iloc[i])
                startTrade = data_to_check[data_to_check["from"]==obj["time_fin"].iloc[i]]["open"].iloc[0]
 
                if (obj["action"].iloc[i] == "put" and float(startTrade) > float(endTrade)):
                    obj["out"].iloc[i] = "win"
                elif (obj["action"].iloc[i] == "call" and float(startTrade) < float(endTrade)):
                    obj["out"].iloc[i] = "win"
                elif (obj["action"].iloc[i] == "put" and float(startTrade) < float(endTrade)):
                    obj["out"].iloc[i] = "lose"
                elif (obj["action"].iloc[i] == "call" and float(startTrade) > float(endTrade)):
                    obj["out"].iloc[i] = "lose"
                elif ( (obj["action"].iloc[i] == "put" or obj["action"].iloc[i] == "call") and float(startTrade) == float(endTrade) ):
                    obj["out"].iloc[i] = "lose"

        return obj

    def indicator_processing(self, df):
        # print("***********************************************************************************************************************")
        # print(df)
        df = pd.DataFrame(df)
        
        df["day"]= df["from"].str[8:11]
        df=df.loc[(df['day'] != "08") & (df['day'] != "09")]
        # print(df)
        # print("before call strategie")
        getStrat = strat.Strategy2()
        outputStrategies = getStrat.calc()

        # listAllMonnaie = ["EURUSD"]
        # listDays = ["03"]
        # print(res)
        listDays = ["03", "04", "05", "06", "07", "10", "11", "12", "13", "14"]
        listAllMonnaie = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        
        for monnaie in listAllMonnaie:
            res = self.trades(df, outputStrategies, monnaie)
            for day in listDays:
                data = res[res["days"] == day]
                newData = data[data["monnaie"] == monnaie]
                data_for_sum = newData[newData["action"] != ""]
                cptr_tot = int(data_for_sum[data_for_sum["out"] == "win"].shape[0]) - int(data_for_sum[data_for_sum["out"] == "lose"].shape[0]) 
                cptrgain = 0
                cptrperte = 0
                output = []
                print("size data : ", newData.shape[0])
                for k in range(newData.shape[0]):
                    if (newData["action"].iloc[k] != "" and newData["out"].iloc[k] == "win"):
                        cptrgain += 1
                        

                    if (newData["action"].iloc[k] != "" and newData["out"].iloc[k] == "lose"):
                        cptrperte += 1
                        cptrgain -= 1
                    
                    if ( cptrgain - cptrperte > 1):
                        print("cptrgain : ", cptrgain)
                        print("cptrperte : ", cptrperte)
                        print("monnaie : ", monnaie)
                        print("date : ", str(newData["time_fin"].iloc[k]))
                        print("nb win : ", data_for_sum[data_for_sum["out"] == "win"].shape[0])
                        print("nb lose : ", data_for_sum[data_for_sum["out"] == "lose"].shape[0])
                        print("cptr_tot : ", cptr_tot)
                        output.append({"cptrgain": cptrgain, "cptrperte": cptrperte, "monnaie" : monnaie, "date" : str(newData["time_fin"].iloc[k]), "cptr_tot": cptr_tot})
                        classeTableCheck = myDb.save_to_db(output, "back_test_thief_s2")
                        classeTableCheck.insert_data()
                        break



                # if ( outputStrategies["action"] != ""):
                #     res = self.trades(df, outputStrategies)
                #     if(res == "win"):
                #         cptrGain += 1
                #     else:
                #         cptrPerte += 1
                #     toSkip = i + int(outputStrategies["delta"])
                #     if(cptrGain - cptrPerte > 1):
                #         goalMonney = df["monnaie"].iloc[i]
                #         goalTps = df["from"].iloc[i]
                #         lesPlusDeux.append({"goalTps":goalTps, "goalMonney":goalMonney})
                        
                        
                        
        # output = {"cptrGain": cptrGain, "cptrPerte": cptrPerte, "goalMonney" : goalMonney, "goalTps" : goalTps, "lesPlusDeux":lesPlusDeux}
       

        # return output

    def computeStrategie(self):
        
        I_want_money = IQ_Option(credentials.login, credentials.mdp2)
        I_want_money.connect()
        allData = []
        listMonnaie = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        # listMonnaie = ["EURUSD", "EURCAD"]
        for monnaie in listMonnaie:
            end_from_time = 1621015200
            
            # end_from_time = 1620064800
            dataByMoney = []
            for i in range(12):
                # 662
                data= I_want_money.get_candles(monnaie, 60, 680, end_from_time)
                for el in data:
                    el["monnaie"] = monnaie
                    el["from"] = datetime.fromtimestamp(el["from"]).strftime("%Y-%m-%d %H:%M")
                    el["to"] = datetime.fromtimestamp(el["to"]).strftime("%Y-%m-%d %H:%M")
                    del el['at']
                    del el['id']
                dataByMoney = data + dataByMoney 
                end_from_time = datetime.strptime(datetime.fromtimestamp(end_from_time).strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M") - timedelta(days=1)
                # print(end_from_time)
                end_from_time=end_from_time.timestamp()
            allData=dataByMoney + allData
            # print(allData)
        df = pd.DataFrame(allData) 
        print("start testing")
        self.indicator_processing(df)



if __name__ == '__main__':
    I_want_money = IQ_Option(credentials.login, credentials.mdp2)
    I_want_money.connect()
    test = MyBot(I_want_money)
    test.computeStrategie()
