import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
import pandas_datareader.data as pdr
yf.pdr_override()

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scipy import stats
from sklearn.metrics import r2_score

import pytz
import datetime as dt
from datetime import date, datetime
import matplotlib.dates as mdates
my_year_month_fmt = mdates.DateFormatter('%d/%m/%y')

class Trend:
    def __init__(self, tickers, pos = None, benchmark = None, inicio = dt.datetime.today().date()-dt.timedelta(365), fim = dt.datetime.today().date()):
        self.inicio = inicio
        self.fim = fim
        self.tickers = tickers
        self.benchmark = benchmark

        if pos == None:
            self.pos = {i:'C' for i in tickers}
        else:
            self.pos = pos

        self.Data = pdr.get_data_yahoo(self.tickers, start=self.inicio, end=self.fim)['Adj Close'].bfill()

        if type(self.Data) == type(pd.Series([], dtype='object')):
            self.Data = pd.DataFrame(self.Data.values, index=self.Data.index,columns=self.tickers)
        if self.benchmark != None:
            if len(self.benchmark) > 1:
                for i in self.benchmark:
                    self.Data[f'Benchmark {i}'] = pdr.get_data_yahoo(i, start=self.inicio, end=self.fim)['Adj Close'].bfill()
                    
            else:
                self.Data['Benchmark'] = pdr.get_data_yahoo(self.benchmark, start=self.inicio, end=self.fim)['Adj Close'].bfill()

        self.Data = self.Data.bfill().fillna(0)

    def retornos(self, tipo = 'pct', dist = ['Long', 'Short']):
        self.retorno = self.Data.pct_change().fillna(0)
        lista = []
        f=0
        if type(self.retorno) == type(pd.Series([], dtype='object')):
            if self.pos[list(self.pos.keys())[0]].capitalize() == 'V':
                self.retorno = self.retorno * -1
        else:
            for i in self.retorno.columns:
                if i in list(self.pos.keys()):
                    if self.pos[i].capitalize() == 'V':
                        self.retorno[i] = self.retorno[i] * -1

        if tipo.capitalize()[0] == 'P': # Return
            return self.retorno
    
        elif tipo.capitalize()[0] == 'A': # Acumulated
            return ((1+self.retorno).cumprod())
    
        elif tipo.capitalize()[0] == 'W': # Weighted Return
            self.retorno['Pesos'] = [1+i for i in range(len(self.retorno))]
            self.retorno['Pesos'] = self.retorno['Pesos']/self.retorno['Pesos'].iloc[-1]
            self.retorno = self.retorno.apply(lambda x: x*self.retorno['Pesos'])
            self.retorno = self.retorno.drop('Pesos', axis=1)
            return self.retorno

        # Exponential Weights Return
        elif tipo.capitalize()[0] == 'E': 
            if type(dist) == type([]) and len(dist) == len([" ", " "]): #standard
                for i in dist:
                    print(1)
                    # If string, must be Long. If Num, must bem int and the max of the list
                    if type(i) == type(str):
                        if str(i).capitalize()[0] == 'L':
                            self.ret_s = self.retorno.ewm(alpha=0.15, min_periods=132, adjust=False).mean()
                        elif str(i).capitalize()[0] == 'S':
                            self.ret_l = self.retorno.ewm(alpha=0.7, min_periods=22, adjust=False).mean()
                        print(1)
                    elif type(i) == type(int()):
                        if i == max(dist):
                            self.ret_l = self.retorno.ewm(alpha=0.7, min_periods=i, adjust=False).mean()
                        elif i == min(dist):
                            self.ret_s = self.retorno.ewm(alpha=0.15, min_periods=i, adjust=False).mean()     
                    else:
                        print(f'ERROR {i} {type(i)}')
                # self.retorno = pd.concat([self.ret_s , self.ret_l], keys=['Long', 'Short'], names=['Tipo'], axis = 1) 
                # return self.retorno
                return self.ret_l, self.ret_s

    def di(self, JGP = False, Date = None):
        self.Date = Date
        if self.Date == None:
            self.Date = pd.to_datetime(self.Data.index).strftime('%d/%m/%y')
        if JGP:
            self.Download = pd.DataFrame(columns = ['DI'])
            self.Download['DI'] = [np.array((.05 * (1/360))-1) for i in range((pd.to_datetime(self.Data.index[-1])-pd.to_datetime(self.Data.index[0])).days)]
        else:
            DI = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=csv&dataInicial={self.Date[0]}&dataFinal={self.Date[-1]}'
            self.Download = pd.read_csv(DI)
            self.Download.columns = ['DI']
            self.Download.index = self.Download.index.str.rstrip(f';"0')
            self.Download['DI'] = self.Download['DI'].str.rstrip(f'"').astype(int)/100000000
        return self.Download

    def formatar(self, valor):
        # Copiado do Edu
        return "{:,.2%}".format(valor)

    def medio(self, dias=5, ret = None):
        if type(dias) == type({}):
            dias = list(dias.values())
        if ret == None:
            self.long, self.short = self.retornos('E', dist=dias)
        return self.long, self.short
        
    def mediana(self, dias=5, ret = None):
        if type(dias) == type({}):
            dias = list(dias.values())
        if ret == None:
            ret = self.retornos('E', dist=dias)
        return ret.rolling(dias).median()
        
    def trend(self, dias = {'Long':126, 'Short':22}):
        med_l, med_s = self.medio(dias=dias)
        self.dif = (med_s-med_l).fillna(0)
        return self.dif, med_l, med_s,  self.retornos('A')
    
    def ordens(self):
        tr = self.trend()
        ordens = pd.DataFrame(columns = tr[2].columns, index = tr[2].index)
        return 1
        # for i in ordens.index:
        #     for _ in ordens.loc[i].values:
        #         if tr[0].loc[i] > 0:
                
        # return ordens
        
    
    # Refazer Trend do Cid: |
    # Fazer Weighted VaR | 
    # Fazer Weighted | Check
    # Entrar a partir de certo coeficiente angular (a partir dos retornos da livre de risco de cada região dos ativos) |

    # Fazer "estabilidade" do C.A. dos retornos (5 dias atras) para 5 dias seguidos e pegar o desvio padrão e validar ou não stop gain |

    #Pegar X23 por cada dia e comparar com cotacao dol BRl (cap. derivativos Ana Clara)
Lista = ['AZUL4.SA', 'EWG', 'BOVA11.SA', 'VALE3.SA', 'SPY', 'XLF', 'XLRE']
Vendidos = ['AZUL4.SA', 'BOVA11.SA', 'SPY', 'XLRE']

PPP = {i:"" for i in Lista}
for i in Lista:
  if i in Vendidos:
    PPP[i] = 'V'
  else:
    PPP[i] = 'C'

x, y, z, w = Trend(Lista, PPP, ['^BVSP']).trend()

print(x, y, z, w)
# y = ((1+y).cumprod())
# # px.area(x).show()
# fig, ax = plt.subplots(1,1,figsize=(12,6))

# for i in z.columns:
#     ax.set_title(i)
#     ax.plot(y['Long'][i])
#     # ax.plot(y['Short'][i])
#     ax.plot(z[i])
#     ax.set_xlim(y['Long'][i].index[0], y['Long'][i].index[-1])
#     # ax.plot(z)
#     plt.show()

# x, y = Trend(Lista, PPP, ['^BVSP']).medio(dias = {'Long':126, 'Short':22})

# print(x)
# print(y)