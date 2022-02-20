import ta
import pandas as pd
import numpy as np
import datetime
import trendln
from tapy import Indicators
import psycopg2
import credentials

class get_all_indicator():
    '''
    This class has been developed to contain all the indicators
    Args:
    data(pandas.Series): dataframe.
    monIndic(dict): it containing action and monnaie.

    return:
        monIndic (dict) : {"monnaie" : "self.monnaie", "action": "call or put or empty"}
        action is gonna containing a call, a put or an empty string  
    '''
    def __init__(self, data, monIndic):
        self.data = data
        self.monIndic = monIndic

    def get_time(self, tps):
        if (tps >= 55 and tps < 59):
            return 59
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

    def isSupport(self, df,i):
        support = df['min'][i] < df['min'][i-1]  and df['min'][i] < df['min'][i+1] \
        and df['min'][i+1] < df['min'][i+2] and df['min'][i-1] < df['min'][i-2]

        return support

    def isResistance(self, df,i):
        resistance = df['max'][i] > df['max'][i-1]  and df['max'][i] > df['max'][i+1] \
        and df['max'][i+1] > df['max'][i+2] and df['max'][i-1] > df['max'][i-2] 

        return resistance

    def isFarFromLevel(self, l, s, levels):
        return np.sum([abs(l-x) < s  for x in levels]) == 0
    
    def loopOverDf(self, pas, df, col, colOut):
        for i in range(df.shape[0]-1, 30, pas):
            if(df[col][i] > 0 and df[col][i-1] < 0 and df[col][i-2] < 0):
                df[colOut].iloc[-1] = "call"
                break
            elif(df[col][i] < 0 and df[col][i-1] > 0 and df[col][i-2] > 0):
                df[colOut].iloc[-1] = "put"
                break
            else:
               df[colOut].iloc[-1] = "neutre" 
        return df


    def ichimoku_indicator(self):
        column_names = ["SSA", "SSB", "tendanceCloudDf", "kujin", "tenkan", "close", "crossingTenkanKijun"]
        df = pd.DataFrame(columns = column_names)
        indicateur = ta.trend.IchimokuIndicator(self.data['max'], self.data['min'], 9, 26, 52)
        indicateurSSB = indicateur.ichimoku_b()
        indicateurSSA = indicateur.ichimoku_a()
        # indicateurKujin = indicateur.ichimoku_base_line()
        # indcateurTenkan = indicateur.ichimoku_conversion_line()
        df["SSA"] = indicateurSSA
        df["SSB"] = indicateurSSB
        # df["kujin"] = indicateurKujin
        # df["tenkan"] = indcateurTenkan
        df["tendanceCloudDf"] = df["SSA"].iloc[-10:] - df["SSB"].iloc[-10:]
        # df["crossingTenkanKijun"] = df["kujin"].iloc[-14:] - df["tenkan"].iloc[-14:]
        df["close"] = self.data["close"]
        df["open"] = self.data["open"]
        # print(self.monIndic["monnaie"], "crossing curve", df["tenkan"].iloc[-1], df["kujin"].iloc[-1], df["crossingTenkanKijun"].iloc[-1])
        # print(self.monIndic["monnaie"], "crossing curve", df["tenkan"].iloc[-2], df["kujin"].iloc[-2], df["crossingTenkanKijun"].iloc[-2])

        # condition_croisement_put = (df["crossingTenkanKijun"].iloc[-1] >0 and
        #                             df["crossingTenkanKijun"].iloc[-2] < 0)

        # condition_croisement_call = (df["crossingTenkanKijun"].iloc[-1] < 0 and
        #                             df["crossingTenkanKijun"].iloc[-2] > 0)

        # condition_cours_dessous = (df["close"].iloc[-1] < df["SSB"].iloc[-1] and
        #                             df["open"].iloc[-1] < df["SSB"].iloc[-1] and
        #                             df["open"].iloc[-1] < df["SSA"].iloc[-1] and
        #                             df["close"].iloc[-1] < df["SSA"].iloc[-1])

        # condition_cours_dessus = (df["close"].iloc[-1] > df["SSB"].iloc[-1] and
        #                             df["close"].iloc[-1] > df["SSA"].iloc[-1] and
        #                             df["open"].iloc[-1] > df["SSB"].iloc[-1] and
        #                             df["open"].iloc[-1] > df["SSA"].iloc[-1]
        #                             )
        # condition_chikou_dessus = (df["close"].iloc[-1] > df["close"].iloc[-26])
        # condition_chikou_dessous = (df["close"].iloc[-1] < df["close"].iloc[-26])
        # condition_nuage_vert = (df["tendanceCloudDf"].iloc[-1] > 0)
        # condition_nuage_rouge = (df["tendanceCloudDf"].iloc[-1] < 0)
        # nowInMinutes = datetime.datetime.now().minute
        # timeMaxToTrade = self.get_time(nowInMinutes)
        # if (condition_croisement_put and condition_cours_dessous and condition_chikou_dessous and (timeMaxToTrade - nowInMinutes) > 8):
        #     monIndic["action"] = "put"
        # elif (condition_croisement_call and condition_cours_dessus and condition_chikou_dessus and (timeMaxToTrade - nowInMinutes) > 8):
        #     monIndic["action"] = "call"
        # self.monIndic["action"] = "put"
        if ((df["open"].iloc[-1] < df["SSB"].iloc[-1] or df["open"].iloc[-2] < df["SSB"].iloc[-2])): # and df["tendanceCloudDf"].iloc[-1] > 0):
            return "put"
        elif ((df["open"].iloc[-1] < df["SSA"].iloc[-1] or df["open"].iloc[-2] < df["SSA"].iloc[-2])): # and df["tendanceCloudDf"].iloc[-1] < 0):
            return "put"
        elif ((df["open"].iloc[-1] > df["SSA"].iloc[-1] or df["open"].iloc[-2] > df["SSA"].iloc[-2])): # and df["tendanceCloudDf"].iloc[-1] > 0):
            return "call"
        elif ((df["open"].iloc[-1] > df["SSB"].iloc[-1] or df["open"].iloc[-2] > df["SSB"].iloc[-2])): # and df["tendanceCloudDf"].iloc[-1] < 0):
            return "call"
        else:
            return ""

    def macd_SR_sma_indicator(self):
        print("start checking indicators")
        listOutput = []
        column_names = ["close", "SMA6", "SMA14", "MACD_diff", "SMA_diff", "MACD_decision", "SMA_decision"]
        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
        indicateur_6_periodes = ta.trend.SMAIndicator(df["close"], 6)
        SMA6 = indicateur_6_periodes.sma_indicator()
        indicateur_14_periodes = ta.trend.SMAIndicator(df["close"], 14)
        SMA14 = indicateur_14_periodes.sma_indicator()
        # SMA6 = indicateur_6_periodes
        df["SMA6"] = indicateur_6_periodes.sma_indicator() # SMA6
        df["SMA14"] = indicateur_14_periodes.sma_indicator() # SMA14
        
        indicateurMACD = ta.trend.MACD(df["close"])
        MACD_diff = indicateurMACD.macd_diff()
        df["MACD_diff"] = indicateurMACD.macd_diff() #MACD_diff
        df["SMA_diff"] = df["SMA6"].iloc[-5:] - df["SMA14"].iloc[-5:]
        self.loopOverDf(-5, df, "MACD_diff", "MACD_decision")
        self.loopOverDf(-2, df, "SMA_diff", "SMA_decision")
        
        chim = self.ichimoku_indicator()
        levelSupport = []
        levelResistance = []
        s =  np.mean(self.data['max'] - self.data['min'])
        for i in range(2,self.data.shape[0]-2):
            if self.isSupport(self.data,i):
                l = self.data['min'].iloc[i]

                if self.isFarFromLevel(l, s, levelSupport):
                    levelSupport.append((l))

            elif self.isResistance(self.data,i):
                l = self.data['max'].iloc[i]

                if self.isFarFromLevel(l, s, levelResistance):
                    levelResistance.append((l))
        myDate = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        nowInMinutes = datetime.datetime.now().minute
        timeMaxToTrade = self.get_time(nowInMinutes)
        if (len(levelSupport) == 0):
            smallDf = df["close"].iloc[-10:]
            levelSupport.append(smallDf.min())
        if (len(levelResistance) == 0):
            smallDf = df["close"].iloc[-10:]
            levelResistance.append(smallDf.max())
        # df["MACD_decision"].iloc[-1] == "call" and
       


        getAllIndicators = Indicators(self.data)
        getAllIndicators.fractals()
        getAllIndicators.alligator()
        dfIndicator = getAllIndicators.df
        existCrossing = df["SMA_decision"].iloc[-1]
        # print("fractale :", dfIndicator["fractals_low"].iloc[-3])
        # print("alligator teeth : ",  dfIndicator["min"].iloc[-3] < dfIndicator["alligator_teeth"].iloc[-3])
        # print("nuage ichimoku : ", chim)

        condition_call = ((dfIndicator["fractals_low"].iloc[-3] or dfIndicator["fractals_low"].iloc[-2]) == True and
                          dfIndicator["min"].iloc[-3] < dfIndicator["alligator_teeth"].iloc[-3] and 
                          existCrossing == "call"  and
                          df["close"].iloc[-1] < levelResistance[-1] and
                          chim == "call" and
                          (timeMaxToTrade - nowInMinutes) > 2)
        # df["MACD_decision"].iloc[-1] == "put" and
        condition_put = ( dfIndicator["fractals_high"].iloc[-3] == True and
                          dfIndicator["max"].iloc[-3] > dfIndicator["alligator_teeth"].iloc[-3] and 
                          existCrossing == "put"  and
                          df["close"].iloc[-1] > levelSupport[-1] and
                          chim == "put" and
                          (timeMaxToTrade - nowInMinutes) > 2)
        listOutput.append({"date_debut":myDate, "monnaie": self.monIndic["monnaie"], "close":df["close"].iloc[-1], "macd":df["MACD_diff"].iloc[-1], "sma":df["SMA_diff"].iloc[-1], "action":"", "gain":"", "win_or_lose":"", "date_fin":""})
        listOutput.append({"date_debut":myDate, "monnaie": self.monIndic["monnaie"], "close":df["close"].iloc[-2], "macd":df["MACD_diff"].iloc[-2], "sma":df["SMA_diff"].iloc[-2], "action":"", "gain":"", "win_or_lose":"", "date_fin":""})

        self.monIndic["listOutput"] = listOutput

        if(condition_call):
            self.monIndic["action"] = "call"
        if(condition_put):
            self.monIndic["action"] = "put"
        return self.monIndic


    def ssb_and_oscillator(self):
        print("start checking indicators ssb_and_oscillator")
        listOutput = []
        column_names = ["close","SSA", "SSB", "oscillator"]
        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
        indicateur_ichi = ta.trend.IchimokuIndicator(self.data['max'], self.data['min'], 9, 26, 52)
        indicateurSSB = indicateur_ichi.ichimoku_b()
        indicateurSSA = indicateur_ichi.ichimoku_a()
        # indicateurKujin = indicateur.ichimoku_base_line()
        # indcateurTenkan = indicateur.ichimoku_conversion_line()
        df["SSA"] = indicateurSSA
        df["SSB"] = indicateurSSB
        
        # SMA6 = indicateur_6_periodes

        indicateurAwesomeOscil = ta.momentum.awesome_oscillator(self.data['max'], self.data['min'], 5, 34)
        df["oscillator"] = indicateurAwesomeOscil
        print(df.tail(5))
        
        levelSupport = []
        levelResistance = []
        s =  np.mean(self.data['max'] - self.data['min'])
        for i in range(2,self.data.shape[0]-2):
            if self.isSupport(self.data,i):
                l = self.data['min'].iloc[i]

                if self.isFarFromLevel(l, s, levelSupport):
                    levelSupport.append((l))

            elif self.isResistance(self.data,i):
                l = self.data['max'].iloc[i]

                if self.isFarFromLevel(l, s, levelResistance):
                    levelResistance.append((l))
        myDate = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        nowInMinutes = datetime.datetime.now().minute
        # timeMaxToTrade = self.get_time(nowInMinutes)
        if (len(levelSupport) == 0):
            smallDf = df["close"].iloc[-10:]
            levelSupport.append(smallDf.min())
        if (len(levelResistance) == 0):
            smallDf = df["close"].iloc[-10:]
            levelResistance.append(smallDf.max())

        condition_call = (df["oscillator"].iloc[-1] > df["oscillator"].iloc[-2] and
                            df["oscillator"].iloc[-2] > df["oscillator"].iloc[-3] and
                            df["oscillator"].iloc[-3] > 0 and
                            df["close"].iloc[-1] > df["SSB"].iloc[-1]and 
                            nowInMinutes < 15)
        condition_put = (df["oscillator"].iloc[-1] < df["oscillator"].iloc[-2] and
                            df["oscillator"].iloc[-2] < df["oscillator"].iloc[-3] and
                            df["oscillator"].iloc[-3] < 0 and
                            df["close"].iloc[-1] < df["SSB"].iloc[-1] and 
                            nowInMinutes < 15 )
                        #   df["close"].iloc[-1] < levelResistance[-1] and
                          
        #                   (timeMaxToTrade - nowInMinutes) > 2)
        # # df["MACD_decision"].iloc[-1] == "put" and
        # condition_put = ( dfIndicator["fractals_high"].iloc[-3] == True and
        #                   dfIndicator["max"].iloc[-3] > dfIndicator["alligator_teeth"].iloc[-3] and 
        #                   existCrossing == "put"  and
        #                   df["close"].iloc[-1] > levelSupport[-1] and
        #                   chim == "put" and
        #                   (timeMaxToTrade - nowInMinutes) > 2)
        # listOutput.append({"date_debut":myDate, "monnaie": self.monIndic["monnaie"], "close":df["close"].iloc[-1], "macd":df["MACD_diff"].iloc[-1], "sma":df["SMA_diff"].iloc[-1], "action":"", "gain":"", "win_or_lose":"", "date_fin":""})
        # listOutput.append({"date_debut":myDate, "monnaie": self.monIndic["monnaie"], "close":df["close"].iloc[-2], "macd":df["MACD_diff"].iloc[-2], "sma":df["SMA_diff"].iloc[-2], "action":"", "gain":"", "win_or_lose":"", "date_fin":""})

        # self.monIndic["listOutput"] = listOutput

        if(condition_call):
            self.monIndic["action"] = "call"
        if(condition_put):
            self.monIndic["action"] = "put"
        return self.monIndic
    
    def request_db(self, monnaie):
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        cur = datetime.datetime.now().strftime("%Y-%m-%d %H")
        previousMinutes = str("{0:0>2}".format(datetime.datetime.now().minute - 1))
        previousDate = "%" + cur + ":" + previousMinutes +  "%"
        df_check_range = pd.read_sql_query('''
                select distinct o_result_fin, ma_result_fin from prediction where 
                prevision = '15 MINUTES' and
                CAST(res_date AS text) LIKE'''+ "'"+previousDate + "'"+ '''
                and monnaie = '''+ "'"+ monnaie + "'"+'''
                
                ''', conn)
        return df_check_range

    
    def check_indicateurs(self):

        self.monIndic["action"] = ""
        # levelSupport = []
        # levelResistance = []
        # s =  np.mean(self.data['max'] - self.data['min'])
        # for i in range(2,self.data.shape[0]-2):
        #     if self.isSupport(self.data,i):
        #         l = self.data['min'].iloc[i]

        #         if self.isFarFromLevel(l, s, levelSupport):
        #             levelSupport.append((l))

        #     elif self.isResistance(self.data,i):
        #         l = self.data['max'].iloc[i]

        #         if self.isFarFromLevel(l, s, levelResistance):
        #             levelResistance.append((l))
        # print(self.monIndic["monnaie"])
        # print(levelSupport)
        # print(levelResistance)
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        nowMinutes = str("{0:0>2}".format(datetime.datetime.now().minute))
        now = str("{0:0>2}".format(datetime.datetime.now().minute))
        previousMinutes = str("{0:0>2}".format(datetime.datetime.now().minute - 1))
        cur = datetime.datetime.now().strftime("%Y-%m-%d %H")
        currentDate = "%" + cur + ":" + now +  "%"
        previousDate = "%" + cur + ":" + previousMinutes +  "%"
        data_buy = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bullish_engulfing = 'True' or
                                bullish_harami = 'True' or
                                hammer = 'True' or
                                morning_star = 'True'
                                ) and (
                                CAST(time_fin AS text) LIKE ''' + "'"+currentDate +"'" + ''' or 
                                CAST(time_fin AS text) LIKE ''' + "'"+ previousDate +"'" +  ''' )
                                and monnaie = '''+ "'"+self.monIndic['monnaie'] + "'"+'''
                                

                                ''', conn)
        
        data_put = pd.read_sql_query('''
                                select distinct monnaie, substring(cast(time_debut as text),0, 17) as time_debut from figures where 
                                (bearish_engulfing = 'True' or
                                bearish_harami = 'True' or
                                hanging_man = 'True' or
                                shooting_star = 'True' or
                                evening_star = 'True'
                                ) and (
                                CAST(time_fin AS text) LIKE''' + "'"+currentDate + "'"+ '''or 
                                CAST(time_fin AS text) LIKE'''+ "'"+previousDate + "'"+ ''' )
                                and monnaie = '''+ "'"+self.monIndic['monnaie'] + "'"+'''
                                
                                ''', conn)

        df_check_range = self.request_db(self.monIndic['monnaie'])

        while df_check_range.shape[0] == 0:
            df_check_range = self.request_db(self.monIndic['monnaie'])

        
        column_names = ["close", "SMA14"]
        df = pd.DataFrame(columns = column_names)
        df["close"] = self.data["close"]
          
        indicateur_14_periodes = ta.trend.SMAIndicator(df["close"], 14)
        SMA14 = indicateur_14_periodes.sma_indicator()
        df["SMA14"] = indicateur_14_periodes.sma_indicator() # SMA14
        # diff = int(str(df["SMA14"].iloc[-4]).split(".")[1][-4:]) - int(str(df["SMA14"].iloc[-1]).split(".")[1][-4:])
        # rsi = ta.momentum.rsi(df['close'], 14)
        # checkRsi = ''
        # if (rsi.iloc[-1] > 65 and rsi.iloc[-1] < 80):
        #     checkRsi = 'resistance'
        # elif (rsi.iloc[-1] > 10 and rsi.iloc[-1] < 35):
        #     checkRsi = 'support'
            
        check_range = df_check_range["o_result_fin"].iloc[-1]
        ma = check_range = df_check_range["ma_result_fin"].iloc[-1]
        timeMaxToTrade = self.get_time(int(nowMinutes)) - int(nowMinutes)
        if ((data_buy.shape[0] > 0 or data_put.shape[0] > 0) and timeMaxToTrade >= 2 and check_range != "NEUTRAL"):
            if("BUY" in ma):
                self.monIndic["action"] = "call"
                self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
            elif ("SELL" in ma):
                self.monIndic["action"] = "put"
                self.monIndic["date"] = data_put["time_debut"].iloc[-1]                
        # if (data_buy.shape[0] > 0 and data_put.shape[0] == 0 and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and df["close"].iloc[-1] > df["SMA14"].iloc[-1] and "BUY" in ma):
        #     self.monIndic["action"] = "call"
        #     self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        # elif (data_buy.shape[0] > 0 and data_buy.shape[0] > data_put.shape[0] and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and df["close"].iloc[-1] > df["SMA14"].iloc[-1] and "BUY" in ma):
        #     self.monIndic["action"] = "call"
        #     self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        # elif (data_put.shape[0] > 0 and data_buy.shape[0] == 0 and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and df["close"].iloc[-1] < df["SMA14"].iloc[-1]  and "SELL" in ma):
        #     self.monIndic["action"] = "put"
        #     self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        # elif (data_put.shape[0] > 0 and data_put.shape[0] > data_buy.shape[0] and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and df["close"].iloc[-1] < df["SMA14"].iloc[-1]  and "SELL" in ma):
        #     self.monIndic["action"] = "put"
        #     self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        

        #print("indicator : ", type(self.monIndic["date"]))
        return self.monIndic


    # print('''
    #                         select distinct monnaie from figures where 
    #                         (bearish_engulfing = 'True' or
    #                         bearish_harami = 'True' or
    #                         shooting_star = 'True' or
    #                         evening_star = 'True') and (
    #                         CAST(time_debut AS text) LIKE''' + "'"+currentDate + "'"+ '''or 
    #                         CAST(time_debut AS text) LIKE'''+ "'"+previousDate + "'"+ ''' )
    #                         and monnaie = '''+ "'"+self.monIndic['monnaie'] + "'"+'''
                            
    #                         ''')
    def get_figures(self):
        
        listOut = []
        conn = psycopg2.connect(user=credentials.user,
                                password=credentials.password,
                                host=credentials.host,
                                port=credentials.port,
                                database=credentials.database)
        nowMinutes = str("{0:0>2}".format(datetime.datetime.now().minute))
        now = str("{0:0>2}".format(datetime.datetime.now().minute - 1))
        previousMinutes = str("{0:0>2}".format(datetime.datetime.now().minute - 2))
        cur = datetime.datetime.now().strftime("%Y-%m-%d %H")
        currentDate = "%" + cur + ":" + now +  "%"
        previousDate = "%" + cur + ":" + previousMinutes +  "%"
        data_buy = pd.read_sql_query('''
                                select distinct monnaie from figures where 
                                (bullish_engulfing = 'True' or
                                bullish_harami = 'True' or
                                hanging_man and
                                
                                morning_star = 'True') and (
                                CAST(time_debut AS text) LIKE ''' + "'"+currentDate +"'" + ''' or 
                                CAST(time_debut AS text) LIKE ''' + "'"+ previousDate +"')"+'''
                                
                                ''', conn)
        
        data_put = pd.read_sql_query('''
                                select distinct monnaie from figures where 
                                (bearish_engulfing = 'True' or
                                bearish_harami = 'True' or
                                shooting_star = 'True' or
                                evening_star = 'True') and (
                                CAST(time_debut AS text) LIKE''' + "'"+currentDate + "'"+ '''or 
                                CAST(time_debut AS text) LIKE'''+ "'"+previousDate + "')"+'''
                                
                                ''', conn)
        allMoneyWithoutCrypto = ["EURUSD", "EURGBP", "GBPJPY", "EURJPY", "GBPUSD", "USDJPY", "AUDCAD", "USDCHF", "AUDUSD", "USDCAD",
                                "AUDJPY", "GBPCAD", "GBPCHF", "GBPAUD", "EURCAD", "EURAUD", "CADJPY", "EURCHF", "GBPNZD"]

        timeMaxToTrade = self.get_time(int(nowMinutes)) - int(nowMinutes)
        if(timeMaxToTrade >= 2 and data_buy.shape[0] > 0):
            myDict = {}
            for i in range(0, data_put.shape[0]):
                if(data_put["monnaie"].iloc[i] in allMoneyWithoutCrypto):
                    myDict["monnaie"] = data_put["monnaie"].iloc[i]
                    myDict["action"] = "put"
                    listOut.append(myDict)
                    myDict = {}
        if(timeMaxToTrade >= 2 and data_buy.shape[0] > 0):
            myDict = {}
            for i in range(0, data_buy.shape[0]):
                if(data_put["monnaie"].iloc[i] in allMoneyWithoutCrypto):
                    myDict["monnaie"] = data_put["monnaie"].iloc[i]
                    myDict["action"] = "call"
                    listOut.append(myDict)
                    myDict = {}
        print(data_put)
        print(data_buy)
        print("listOut : ", listOut)
        return listOut
       





  
        if (data_buy.shape[0] > 0 and data_put.shape[0] == 0 and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and ma != "NEUTRAL" and ((rsi < 70 and rsi > 60) or (rsi < 35 and rsi > 20)) and tendanceRsi == "hausse"):
            listBougies = df["close"].values.tolist()
            sma55 = SMA(period = 55, input_values = listBougies)
            ema25 = EMA(period = 25, input_values = listBougies)
            listeEma25 = ema25[-6:]
            listeSma55 = sma55[-6:]
            diffEma = [listeEma25[i] - listeSma55[i] for i in range(0, 5)]
            if (diffEma[0] < 0 and diffEma[-1] > 0):
                self.monIndic["action"] = "call"
                self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        elif (data_buy.shape[0] > 0 and data_buy.shape[0] > data_put.shape[0] and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and ma != "NEUTRAL" and ((rsi < 70 and rsi > 60) or (rsi < 35 and rsi > 20)) and tendanceRsi == "hausse"):
            listBougies = df["close"].values.tolist()
            ema200 = EMA(period = 200, input_values = listBougies)
            ema25 = EMA(period = 25, input_values = listBougies)
            listeEma25 = ema25[-6:] 
            listeEma200 = ema200[-6:]
            diffEma = [listeEma25[i] - listeEma200[i] for i in range(0, 5)]
            if (diffEma[0] < 0 and diffEma[-1] > 0):    
                self.monIndic["action"] = "call"
                self.monIndic["date"] = data_buy["time_debut"].iloc[-1]
        elif (data_put.shape[0] > 0 and data_buy.shape[0] == 0 and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and ma != "NEUTRAL" and ((rsi > 70 and rsi > 60) or (rsi < 35 and rsi > 20)) and tendanceRsi == "baisse"):
            listBougies = df["close"].values.tolist()
            ema200 = EMA(period = 200, input_values = listBougies)
            ema25 = EMA(period = 25, input_values = listBougies)
            listeEma25 = ema25[-6:] 
            listeEma200 = ema200[-6:]
            diffEma = [listeEma25[i] - listeEma200[i] for i in range(0, 5)]
            if (diffEma[0] > 0 and diffEma[-1] < 0):            
                self.monIndic["action"] = "put"
                self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        elif (data_put.shape[0] > 0 and data_put.shape[0] > data_buy.shape[0] and timeMaxToTrade >= 2 and check_range != "NEUTRAL" and ma != "NEUTRAL" and ((rsi > 70 and rsi > 60) or (rsi < 35 and rsi > 20)) and tendanceRsi == "baisse"):
            listBougies = df["close"].values.tolist()
            ema200 = EMA(period = 200, input_values = listBougies)
            ema25 = EMA(period = 25, input_values = listBougies)
            listeEma25 = ema25[-6:] 
            listeEma200 = ema200[-6:]
            diffEma = [listeEma25[i] - listeEma200[i] for i in range(0, 5)]
            if (diffEma[0] > 0 and diffEma[0] <0):            
                self.monIndic["action"] = "put"
                self.monIndic["date"] = data_put["time_debut"].iloc[-1]
        

        #print("indicator : ", type(self.monIndic["date"]))
        return self.monIndic


   