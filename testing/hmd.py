import sys
from iqoptionapi.stable_api import IQ_Option
import time
import pandas as pd
from datetime import datetime, timedelta
from multiprocessing import  Pool, Process
import threading
from .. import credentials
sys.path.append('E:\\users\houssem\\trading_analysis\\testing')
import strategies as strat


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
        end_from_time = 1621015200
        dataByMoney = []
        for i in range(12):
            #662
            data= I_want_money.get_candles(self.monnaie, 60, 662, end_from_time)
            for el in data:
                el["monnaie"] = self.monnaie
                el["from"] = datetime.fromtimestamp(el["from"]).strftime("%Y-%m-%d %H:%M")
                el["to"] = datetime.fromtimestamp(el["to"]).strftime("%Y-%m-%d %H:%M")
                del el['at']
                del el['id']
            end_from_time = datetime.strptime(datetime.fromtimestamp(end_from_time).strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M") - timedelta(days=1)
            end_from_time=end_from_time.timestamp()
            dataByMoney.append(data)
            
            # dataByMoney = data + dataByMoney
        # data= I_want_money.get_candles(self.monnaie, 60, 60, end_from_time)
        self.lock.release()
        for x in dataByMoney:
            temporaryList.append(x)
        # temporaryList.append(self.monnaie)
        self.listOutput.append(temporaryList)
        
        


def trades(data, obj):
    # print(obj)
    out = ""
    timeEndTrade = str(datetime.strptime(obj["date"], "%Y-%m-%d %H:%M") + timedelta(minutes=int(obj["delta"])))[:-3]
    endTrade = data[data["from"]==timeEndTrade]["open"]
    startTrade = data[data["from"]==obj["date"]]["open"]
    if (obj["action"] == "put" and float(startTrade) > float(endTrade)):
        out = "win"
    elif (obj["action"] == "call" and float(startTrade) < float(endTrade)):
        out = "win"
    elif (obj["action"] == "put" and float(startTrade) < float(endTrade)):
        out = "lose"
    elif (obj["action"] == "call" and float(startTrade) > float(endTrade)):
        out = "lose"
    else:
        out = "lose"

    return out

def indicator_processing(df):
    # print("***********************************************************************************************************************")
    # print(df)
    df = pd.DataFrame(df)
    
    df["day"]= df["from"].str[8:11]
    df=df.loc[(df['day'] != "08") & (df['day'] != "09")]
    # print(df)
    cptrGain = 0
    cptrPerte = 0
    goalMonney = df["monnaie"].iloc[-1]
    dayToCheck = "00"
    toSkip = -1
    goalTps = df["from"].iloc[1]
    lesPlusDeux = []
    # print(df)
    for i in range(3, df.shape[0]):
        data = df[i-3 : i]
        if (i >= toSkip):
            # print("before call strategie")
            getStrat = strat.Strategy(data)
            outputStrategies = getStrat.stZaineb()
            if ( outputStrategies["action"] != ""):
                res = trades(df, outputStrategies)
                if(res == "win"):
                    cptrGain += 1
                else:
                    cptrPerte += 1
                toSkip = i + int(outputStrategies["delta"])
                if(cptrGain - cptrPerte > 1):
                    goalMonney = df["monnaie"].iloc[i]
                    goalTps = df["from"].iloc[i]
                    lesPlusDeux.append({"goalTps":goalTps, "goalMonney":goalMonney})
                    # print("le + 2 est atteint pour la paire ", goalMonney , " à ", goalTps)
                       
                    
    output = {"cptrGain": cptrGain, "cptrPerte": cptrPerte, "goalMonney" : goalMonney, "goalTps" : goalTps, "lesPlusDeux":lesPlusDeux}
    print(output)
    return output



# https://www.epochconverter.com/
# coller Epoch timestamp en tant que dernier parametre dans get_candles
class MyBot():
    indicator_processing = staticmethod(indicator_processing)
    def __init__(self, I_want_money):
        self.I_want_money=I_want_money

    def computeStrategie(self):
        
        I_want_money = IQ_Option(credentials.login, credentials.mdp2)
        I_want_money.connect()
        allData = []
        # listMonnaie = ["EURUSD", "EURCAD", "EURAUD", "AUDUSD", "GBPCAD", "EURGBP", "GBPJPY",  "GBPUSD", "USDCAD", "AUDCAD", "GBPAUD", "AUDJPY", "EURJPY", "GBPCHF"]
        listMonnaie = ["GBPCHF"]
        # for monnaie in listMonnaie:
        #     end_from_time = 1620936000
        #     dataByMoney = []
        #     for i in range(10):
        #         # 662
        #         data= I_want_money.get_candles(monnaie, 60, 100, end_from_time)
        #         for el in data:
        #             el["monnaie"] = monnaie
        #             el["from"] = datetime.fromtimestamp(el["from"]).strftime("%Y-%m-%d %H:%M")
        #             el["to"] = datetime.fromtimestamp(el["to"]).strftime("%Y-%m-%d %H:%M")
        #             del el['at']
        #             del el['id']
        #         dataByMoney = data + dataByMoney 
        #         end_from_time = datetime.strptime(datetime.fromtimestamp(end_from_time).strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M") - timedelta(days=1)
        #         # print(end_from_time)
        #         end_from_time=end_from_time.timestamp()
        #     allData = dataByMoney + allData


        # df = allData

        listOutput = []
        listProcess= []
        lock=threading.Lock()
        # getDataFromIQ= getDataFromIQ(I_want_money, "","", )
        print("get data")
        for i, monnaie in enumerate(listMonnaie):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = getDataFromIQ(I_want_money, monnaie, lock, listOutput)
        for el in listProcess:
            eval(el).start()
        for el in listProcess:
            eval(el).join()

        pool = Pool(processes=8)
        finalOut = []
       
        print("start testing")
        # print(listOutput)
        # concat_list= []
        # for element in listOutput:
        #     for subElemlemt in element:
        #         print("**********************************************************************************************************")
        #         print(subElemlemt)
        #         concat_list.append(subElemlemt)
        # print(concat_list)
        for element in listOutput:
            for subElement in element:
                # print(subElemlemt)
                pool_output = Process(target=MyBot.indicator_processing, args=(subElement,))
                finalOut.append(pool_output)
        for j in finalOut:
            j.start()
            time.sleep(0.1)
            j.join()
            # pool.close()
            # pool.join()
            # finalOut.append(pool_output)
        # print(j)
        # print(finalOut)
        # print(pool_output)

if __name__ == '__main__':
    I_want_money = IQ_Option(credentials.login, credentials.mdp2)
    I_want_money.connect()
    test = MyBot(I_want_money)
    test.computeStrategie()
