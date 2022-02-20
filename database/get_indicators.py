import ta
import pandas as pd
# data= I_want_money.get_candles(self.monnaie, 60, 20, end_from_time)

class trend():
    def __init__(self, data):
        self.df = data
    
    def indic_bollinger(self, periode):
        return ta.volatility.BollingerBands(self.df['close'], 14, periode)[19]

    def indic_rsi(self):
        return ta.momentum.rsi(self.df['close'], 14)[19]

    def indic_ema(self, periode):
        return ta.trend.EMAIndicator(self.df['close'], periode)[19]


def indicator_processing(data):
    outputBolliger = ""
    close = []
    for el in data:
        close.append(el['close'])
    df=pd.DataFrame(close, columns=['close']) 
    rsi = ta.momentum.rsi(df['close'], 14)
    bandBol = ta.volatility.BollingerBands(df['close'], 14, 2)
    indicatorSupBandDol = bandBol.bollinger_hband_indicator()
    print(rsi[19],"test rsi and bollinger pour", " ", indicatorSupBandDol[19])

    if ((indicatorSupBandDol[19] > 0 or indicatorSupBandDol[18] > 0) and rsi[19]> 81):
        return outputBolliger


'''
ichimoku : indicateur de tendance
il se constitue via 5 courbes
donne la dynamique des differentes monnaies
tenkan = point moyen des prix des 9 dernières bougies, elle nous alerte sur la santé d'un mvmt 
et de la la puissance du mvmt. plus c'est incliné plus c'est puissant

'''