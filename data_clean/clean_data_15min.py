import pandas as pd
import numpy as np
import psycopg2
import json
import datetime
import matplotlib.pyplot as plt
import credentials

# config to connect my DB
conn = psycopg2.connect(user=credentials.user2,
                             password=credentials.password2,
                             host=credentials.host2,
                             port=credentials.port2,
                             database=credentials.database2)

# create 2 dataframe for cleaning 
dfReelData = pd.read_sql_query('''select * from data_candles  where monnaie = 'GBPJPY' ''', conn)

dfPredictedData = pd.read_sql_query('''select * from prediction  where monnaie = 'GBPJPY' and prevision = '5 minutes' ''', conn)

def outputTrad(open, close):
    if(open > close):
        return "sell"
    elif(open < close):
        return "buy"
def remSeconds(tps):
    return tps.strftime('%Y-%m-%d %H:%M')

def compteur(x, y):
    if y.upper() in x:
        return 1
    else:
        return 0
def test(x):
    return x+ datetime.timedelta(0, 300)

def compare(nb):
    if nb > 0:
        return 1
    else:
        return 0
def difference(cond, res, ouverture, fermeture):
    if(cond > 0 and res == "buy"):
        return  fermeture - ouverture
    elif (cond > 0 and res == "sell"):
        return ouverture - fermeture
def percentage(x):
    if x is None:
        return 0
    else:
        return x * 1000 #"{:.1%}".format(x) 
dfReelData['time_end_cand15'] = dfReelData['time_start_cand'].apply(test)


# on ajoute le mm temps de debut pour toutes les bougies 
# on met la mm ouverture pour toutes les bougies du mm 5 min
for i in range(0, dfReelData.shape[0]-12, 12):
    tps = dfReelData["time_start_cand"].iloc[i] + datetime.timedelta(0, 300)
    open = dfReelData["open"].iloc[i]
    for x in range(i, i+12):
        dfReelData["time_end_cand15"].iloc[x] = tps
        dfReelData["open"].iloc[x] = open
# remove seconds from dates
dfReelData['time_end_cand'] = dfReelData['time_end_cand'].apply(remSeconds)
dfReelData['time_start_cand'] = dfReelData['time_start_cand'].apply(remSeconds)
dfReelData['time_end_cand15'] = dfReelData['time_end_cand15'].apply(remSeconds)

# dfReelData.rename(columns={'time_start_cand': 'res_date'}, inplace=True)
# dire si la bougie est gagnante ou pas par rapport au prix d'ouverture des 5 min
dfReelData["result_trad"] = np.vectorize(outputTrad)(dfReelData["open"], dfReelData["close"])
# remove seconds from dates
dfPredictedData['res_date'] = dfPredictedData['res_date'].apply(remSeconds)
# jointure sur le temps 
dfPredictedData = dfPredictedData.merge(dfReelData[['result_trad', 'open', 'close', 'time_end_cand15']], how='inner', left_on='res_date', right_on='time_end_cand15')

# dfPredictedData= dfPredictedData[dfPredictedData['g_result_fin'].str.contains("STRONG")]
# compter le nombre de fois ou ilya une bonne prediction
dfPredictedData["croisement"] = np.vectorize(compteur)(dfPredictedData["g_result_fin"], dfPredictedData["result_trad"])

# calculer la difference des pips
dfPredictedData["diff"] = np.vectorize(difference)(dfPredictedData["croisement"], dfPredictedData["result_trad"],  dfPredictedData["open"],  dfPredictedData["close"])
dfPredictedData['diff'] = dfPredictedData['diff'].apply(percentage)

# supprimer les doublons par rapport a la colonne temps 
dfPredictedData.drop('time_end_cand15', inplace=True, axis=1)


# for i in range(0, dfReelData.shape[0]-12, 12):
# somme de nombre de fois ou il y a un moment gagnant 
dfPredictedData['somme'] = dfPredictedData['croisement'].groupby(dfPredictedData['res_date']).transform('sum')
dfPredictedData['maximum'] = dfPredictedData['diff'].groupby(dfPredictedData['res_date']).transform('max')
dfPredictedData['moy'] = dfPredictedData['diff'].groupby(dfPredictedData['res_date']).transform(np.mean)

dfPredictedData = dfPredictedData.drop_duplicates(subset=["res_date"], keep="first")
dfPredictedData["cptr"] = np.vectorize(compare)(dfPredictedData["somme"])
dfPredictedData = dfPredictedData.sort_values(by=['res_date'])

tot = dfPredictedData.shape[0]
sommeIdent = dfPredictedData["cptr"].sum(axis = 0, skipna = True)
percent = (sommeIdent/tot)
print(dfPredictedData.head(50))
print("the percend is :", percent*100 , "%")
print(dfPredictedData["moy"].sum()/tot)
df = dfPredictedData[['o_result_fin', 'ma_result_fin', 'g_result_fin']]
df = df.drop_duplicates(subset=['o_result_fin', 'ma_result_fin', 'g_result_fin'], keep="first")
print(df)
ax = dfPredictedData.plot(kind='bar',x='res_date',y='moy', rot=90, title="repartition des moyennes", bottom=0.25)
xticks = ax.xaxis.get_major_ticks()
for i,tick in enumerate(xticks):
    if i%3 != 0:
        tick.label1.set_visible(False)

plt.show()

# dfPredictedData[(dfPredictedData.prevision != "15 minute")]
# dfPredictedData.drop(dfPredictedData.index[dfPredictedData['prevision'] == 0], inplace = True)
# dfPredictedData = dfPredictedData.drop(dfPredictedData[dfPredictedData['prevision'] !="5 minutes"].index)
#     dfReelData["tot"].iloc[x] = tps



# dfPredictedData= dfPredictedData[dfPredictedData['o_result_fin'].str.contains("STRONG")]

# dfPredictedData= dfPredictedData[dfPredictedData['ma_result_fin'].str.contains("STRONG")]



# print(dfPredictedData.head(50))
# dfPredictedData["cptr"] = np.vectorize(compteur)(dfPredictedData["g_result_fin"], dfPredictedData["result_trad"])
# sommeIdent = dfPredictedData["cptr"].sum(axis = 0, skipna = True)
# percent = (sommeIdent/dfPredictedData.shape[0])*100 

# print("the percend is :", percent, "%")