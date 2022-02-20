from iqoptionapi.stable_api import IQ_Option
from datetime import datetime
from multiprocessing import Process, Queue, Pool, Manager
import threading
import pandas as pd
import psycopg2
import pytz
import time
import sys
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
# sys.path.append('E:\\users\houssem\\trading_analysis\\database')
# import testDb as myDb
import itertools
from candlestick.candlestick import *
import psycopg2
from .. import credentials

class myDb():
    def __init__(self, listOutput, table):
        self.listOutput = listOutput
        self.table = table
    def insert_data(self):
        columns = " "
        allKeys = list(self.listOutput[0].keys())
        columns = ', '.join([str(elem)  for elem in allKeys]) 
        values =  ', '.join(["%("+str(elem) + ")s" for elem in allKeys]) 
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        
        cursor = conn.cursor()
        postgreSQL_select_Query = "INSERT INTO "+ self.table + " (" + columns +") VALUES (" + values+ ");"
        cursor.executemany(postgreSQL_select_Query, self.listOutput)
        conn.commit()
        conn.close()
        print("commit at ", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


class get_data_multithread(threading.Thread):
    def __init__(self,account,monnaie, lock, listOutput):
        threading.Thread.__init__(self)
        self.monnaie=monnaie
        self.account = account
        self.listOutput = listOutput
        self.lock = lock
    def run(self):
        tz_Paris = pytz.timezone('Europe/Paris')
        self.lock.acquire()
        print("start step get data from IQ")
        end_from_time = time.time()
        I_want_money=self.account
        data= I_want_money.get_candles(self.monnaie, 60, 4, end_from_time)
       
        for el in data:
            el["monnaie"] = self.monnaie
            el["from"] = datetime.fromtimestamp(el["from"]) 
            el["to"] = datetime.fromtimestamp(el["to"])
            del el['at']
            del el['id']
            del el['volume']
        self.lock.release()
        self.listOutput.append(data)

def figure_candle_processing(data):
    df = pd.DataFrame(data)
    df.rename(columns={'min': 'low', 'max': 'high', 'from': 'time_debut', 'to': 'time_fin'}, inplace=True)
    allPatterns = ["hammer"]
    for pattern in allPatterns:
        df[pattern] = eval(pattern)(df, target=pattern)[pattern]
    return df

class main():
    figure_candle_processing = staticmethod(figure_candle_processing)
    def __init__(self, account, login, pwd):
        self.account = account
        self.login = login
        self.pwd = pwd
    
    def getFiguresAndWriteToDb(self):

        allMoneyWithoutCrypto = ["EURUSD"]
        I_want_money = self.account
        listOutput = []
        listProcess= []
        lock=threading.Lock()
        for i, monnaie in enumerate(allMoneyWithoutCrypto):
            process = "process" + str(i)
            listProcess.append(process)
            globals()[process] = get_data_multithread(I_want_money, monnaie, lock, listOutput)
        for el in listProcess:
            eval(el).start()
        for el in listProcess:
            eval(el).join()
        
        # merged = list(itertools.chain(*listOutput))
        
        
        # print(merged)
        pool = Pool(processes=2)
        
        pool_output = pd.concat(pool.map(main.figure_candle_processing, listOutput, chunksize=5))
        pool.close()
        pool.join()
        print(pool_output)
        pool_output = pool_output.to_dict('records')
        classDb = myDb(pool_output, "figures")
        # classDb.insert_data()
        now = 60-datetime.now().second
        print("time to sleep ", now, " seconds")
        time.sleep(now)



if __name__ == '__main__':  # If it's executed like a script (not imported)
    iq = IQ_Option(credentials.login,credentials.mdp2)
    iq.connect()
    print("connexion succed !")
    getMethod= main(iq, credentials.login,credentials.mdp2)
    while True:
        getMethod.getFiguresAndWriteToDb()