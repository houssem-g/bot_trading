import pandas as pd
import numpy as np
import psycopg2
import json
import credentials

# config to connect my DB
conn = psycopg2.connect(user=credentials.user2,
                             password=credentials.user2,
                             host=credentials.host2,
                             port=credentials.port2,
                             database=credentials.database2)

# create 2 dataframe for cleaning
dfReelData = pd.read_sql_query('''select * from data_candles where monnaie = 'GBPJPY' ''', conn)

dfPredictedData = pd.read_sql_query('''select * from prediction  where monnaie = 'GBPJPY' ''', conn)

def outputTrad(open, close):
    if(open > close):
        return "sell"
    else:
        return "buy"
def remSeconds(tps):
    return tps.strftime('%Y-%m-%d %H:%M')

def compteur(x, y):
    if y.upper() in x:
        return 1
    else:
        return 0
 
#remove seconds from dates
dfReelData['time_start_in_min'] = dfReelData['time_start_cand'].apply(remSeconds)
for i in range(0, dfReelData.shape[0]-1):
    if(dfReelData['time_start_in_min'].iloc[i] == dfReelData['time_start_in_min'].iloc[i+1]):
        dfReelData["close"].iloc[i] = dfReelData["close"].iloc[i+1]

#remove unused data
dfReelData.drop('time_start_in_min', inplace=True, axis=1)

# remove seconds from dates
dfReelData['time_end_cand'] = dfReelData['time_end_cand'].apply(remSeconds)
dfReelData['time_start_cand'] = dfReelData['time_start_cand'].apply(remSeconds)
# dfReelData.rename(columns={'time_start_cand': 'res_date'}, inplace=True)
# add column result buy or sell
dfReelData["result_trad"] = np.vectorize(outputTrad)(dfReelData["open"], dfReelData["close"])

#remove duplicates based on date start
dfReelData = dfReelData.drop_duplicates(subset=["time_start_cand"], keep="first")

# remove seconds from dates
dfPredictedData['res_date'] = dfPredictedData['res_date'].apply(remSeconds)
dfPredictedData = dfPredictedData.merge(dfReelData[['result_trad', 'time_start_cand']], how='inner', left_on='res_date', right_on='time_start_cand')
dfPredictedData.drop('time_start_cand', inplace=True, axis=1)
dfPredictedData[(dfPredictedData.prevision != "1 minute")]
# dfPredictedData.drop(dfPredictedData.index[dfPredictedData['prevision'] == 0], inplace = True)
dfPredictedData = dfPredictedData.drop(dfPredictedData[dfPredictedData['prevision'] !="1 minute"].index)
# dfPredictedData = dfPredictedData.drop(dfPredictedData[dfPredictedData['g_result_fin'].str.contains("STRONG")].index)


# dfPredictedData= dfPredictedData[dfPredictedData['o_result_fin'].str.contains("STRONG")]

dfPredictedData= dfPredictedData[dfPredictedData['ma_result_fin'].str.contains("STRONG")]

dfPredictedData= dfPredictedData[dfPredictedData['g_result_fin'].str.contains("STRONG")]
print(dfPredictedData.head(50))
dfPredictedData["cptr"] = np.vectorize(compteur)(dfPredictedData["g_result_fin"], dfPredictedData["result_trad"])
sommeIdent = dfPredictedData["cptr"].sum(axis = 0, skipna = True)
percent = (sommeIdent/dfPredictedData.shape[0])*100 

print("the percend is :", percent, "%")