from tradingview_ta import TA_Handler, Interval, Exchange
from datetime import datetime
import threading
from threading import Thread
import psycopg2
import pytz
import credentials

class buy_multiThread (threading.Thread):
    def __init__(self,monnaie,screener,exchange,interval, listOutput,crypto):
        threading.Thread.__init__(self)
        self.monnaie=monnaie
        self.screener=screener
        
        if(crypto == True):
            self.exchange=exchange
        else:
            self.exchange=eval(exchange)
        self.interval=interval
        self.listOutput = listOutput
        # self.lock = lock
    def run(self):
        tz_Paris = pytz.timezone('Europe/Paris')
        exchangeDollarsEuros1=TA_Handler(symbol=self.monnaie, screener=self.screener, exchange=self.exchange, interval=eval(self.interval))
        getData1Minute = exchangeDollarsEuros1.get_analysis()
        prevision = ' '.join(self.interval.split("_")[-2:])
        rsi = getData1Minute.indicators["RSI"]
        dict1Minute = {'res_date': datetime.now(tz_Paris).strftime("%Y/%m/%d %H:%M:%S"), 'monnaie': self.monnaie, 'prevision': prevision, 'rsi':rsi}
        newKeysSummary = ['g_result_fin', 'g_buy', 'g_sell', 'g_neutral']
        
        
        outputSummary = getData1Minute.summary
        # self.lock.acquire()
        # outputSummary.popitem()
        for i, n_key in enumerate(newKeysSummary):
            outputSummary[n_key] = outputSummary.pop(list(outputSummary.keys())[0])
        # self.lock.release()
        newKeysMa = ['ma_result_fin', 'ma_buy', 'ma_sell', 'ma_neutral']
        outputMa = getData1Minute.moving_averages
        # self.lock.acquire()
        outputMa.popitem()
        for i, n_key in enumerate(newKeysMa):
            outputMa[n_key] = outputMa.pop(list(outputMa.keys())[0])
        # self.lock.release()
        newKeysOscillateur = ['o_result_fin', 'o_buy', 'o_sell', 'o_neutral']
        outputOscillateur = getData1Minute.oscillators
        # self.lock.acquire()
        outputOscillateur.popitem()
        for i, n_key in enumerate(newKeysOscillateur):
            outputOscillateur[n_key] = outputOscillateur.pop(list(outputOscillateur.keys())[0])
        # self.lock.release()
        dict1Minute.update(outputSummary)
        dict1Minute.update(outputMa)
        dict1Minute.update(outputOscillateur)
        self.listOutput.append(dict1Minute)
        # return dict1Minute
 

listOutput = []
listProcess  = []
listInterval = ["Interval.INTERVAL_1_MINUTE", "Interval.INTERVAL_5_MINUTES", "Interval.INTERVAL_15_MINUTES"]
listMonnaie = ["EURUSD", "EURGBP", "GBPJPY", "EURJPY", "GBPUSD", "USDJPY", "AUDCAD", "USDCHF", "AUDUSD", "USDCAD",
                "AUDJPY", "GBPCAD", "GBPCHF", "GBPAUD", "EURCAD", "EURAUD", "CADJPY", "EURCHF", "GBPNZD","BTCUSD",
                "ETHUSD", "LTCUSD", "XLMUSD", "BTGUSD", "QTMUSD", "OMGUSD","XRPUSD", "TRXUSD", "EOSUSD",
                "ZECUSD", "ETCUSD", "DSHUSD"]


#"BCHUSD": "BITSTAMP"
forex = "forex"
exchange="Exchange.FOREX"
crypto = False
# lock=threading.Lock()
for i , monnaie in enumerate(listMonnaie):
    if monnaie == "BTCUSD":
        crypto = True
        forex = "CRYPTO"
        exchange= "BITFINEX"
    for index, interval in enumerate(listInterval):
        process = "process" + str(index) +"_" + str(i)
        listProcess.append(process)
        globals()[process] = buy_multiThread(monnaie, forex, exchange,interval, listOutput, crypto)
for el in listProcess:
    eval(el).start()
for el in listProcess:
    eval(el).join()

print(listOutput)
# conn = psycopg2.connect(user=credentials.user3,
#                             password=credentials.password,
#                             host=credentials.host2,
#                             port=credentials.port,
#                             database=credentials.database3)
# cursor = conn.cursor()

# postgreSQL_select_Query = """INSERT INTO prediction (res_date, monnaie, prevision, g_result_fin, g_sell, g_buy, g_neutral, o_result_fin, o_sell, o_buy, o_neutral, ma_result_fin, ma_sell, ma_buy, ma_neutral) VALUES (%(res_date)s, %(monnaie)s,%(prevision)s, %(g_result_fin)s, %(g_sell)s, %(g_buy)s, %(g_neutral)s, %(o_result_fin)s, %(o_sell)s, %(o_buy)s, %(o_neutral)s, %(ma_result_fin)s, %(ma_sell)s, %(ma_buy)s, %(ma_neutral)s);"""
# cursor.executemany(postgreSQL_select_Query, listOutput)
# conn.commit()
# conn.close()
print("commit at ", datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


