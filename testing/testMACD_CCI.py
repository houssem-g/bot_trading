import sys
from iqoptionapi.stable_api import IQ_Option
import time
import pandas as pd
from datetime import datetime, timedelta
from multiprocessing import  Pool, Process
import threading
import warnings
pd.set_option('display.max_rows', 500)
from pandas.core.indexes.base import Index
sys.path.append('E:\\users\houssem\\trading_analysis\\testing')
sys.path.append('E:\\users\houssem\\trading_analysis\\database')
import strat_macd_cci as strat
import write_to_db as myDb
from .. import credentials

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
        
        df["day"]= df["from"].str[8:10]
        df["minutes"]= df["from"].str[14:16]
        df["months"]= df["from"].str[5:7]
        df=df.loc[(df['day'] != "08") & (df['day'] != "09") & (df['day'] != "15") & (df['day'] != "16") & (df['day'] != "22") & (df['day'] != "23")
                & (df['day'] != "29") & (df['day'] != "30")]
        
        # print("before call strategie")
        # print(df)
        getStrat = strat.get_indicator(df)
        outputStrategies = getStrat.macd_cci_indicator()

        # print(outputStrategies)
        listDays = ["01", "02", "03", "04", "05", "06", "07", "10", "11", "12", "13", "14", "17", "18",
                    "19", "20", "21", "24", "25", "26", "27", "28"]
        listMonths = ["05", "06"]
        for month in listMonths:
            outputStrategies = outputStrategies[outputStrategies["months"] == month]
            outputStrategies = outputStrategies.reset_index()
            for day in listDays:
                data = outputStrategies[outputStrategies["days"] == day]
                data = data.reset_index()
                data_for_sum = data[data["fin"] != "neutre"]
                data_for_sum = data[data["fin"] != "NaN"]
                # data_for_sum = data_for_sum.reset_index()
                cptr_tot = int(data_for_sum[data_for_sum["fin"] == "win"].shape[0]) - int(data_for_sum[data_for_sum["out"] == "lose"].shape[0]) 
                cptrgain = 0
                cptrperte = 0
                # for i in range(1, df["close"].shape[0]):
                #     if (data_for_sum["fin"].iloc[i]):
                output = []
                print(cptr_tot)
                print(data_for_sum)
                data_for_sum = data_for_sum.reset_index()
                for k in range(0, data_for_sum.shape[0]):
                    print(data_for_sum["out"].iloc[k])
                    if (data_for_sum["out"].iloc[k] == "win"):
                        cptrgain += 1
                        print("+1")
                    if (data_for_sum["out"].iloc[k] == "lose"):
                        cptrperte += 1
                    
                    if ( cptrgain - cptrperte > 1):
                        output.append({"cptrgain": cptrgain, "cptrperte": cptrperte, "monnaie" : data_for_sum["monnaie"].iloc[k], "date" : str(data_for_sum["from"].iloc[k]), "cptr_tot": cptr_tot})
                        classeTableCheck = myDb.save_to_db(output, "back_test_thief_s2")
                        classeTableCheck.insert_data()
                        break


 

    def computeStrategie(self):
        
        I_want_money = IQ_Option(credentials.login, credentials.mdp2)
        I_want_money.connect()
        allData = []
        # listMonnaie = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        listMonnaie = ["EURUSD"]
        for monnaie in listMonnaie:
            end_from_time = 1622829600
            
            dataByMoney = []
            for i in range(33):
                # 662
                data= I_want_money.get_candles(monnaie, 60, 662, end_from_time)
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
        # print(df)
        self.indicator_processing(df)



if __name__ == '__main__':
    I_want_money = IQ_Option(credentials.login, credentials.mdp2)
    I_want_money.connect()
    test = MyBot(I_want_money)
    test.computeStrategie()
