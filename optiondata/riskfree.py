import pandas as pd
import numpy as np 
from scipy.interpolate import InterpolatedUnivariateSpline as interpol
from datetime import datetime

# source = http://iborate.com/usd-libor/
# Libor rates 


def create_libor():
	df_libor = pd.read_csv("LIBOR_USD.csv")
	cols = ['date', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
	df_libor.columns = cols
	df_libor['date'] = pd.to_datetime(df_libor['date'])
	df_libor.set_index('date',inplace=True)
	cols_wo = ['ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
	df_libor[cols_wo] = df_libor[cols_wo].round(2)

	# add missing dates with ffill
	df_libor = df_libor.sort_index()
	idx = pd.date_range('2006-01-01', '2019-07-25')
	df_libor = df_libor.reindex(idx, method="ffill")

# 	store df_libor in csv
	df_libor.to_csv("libor_full.csv")
	print('df_libor stored to csv....')
	
	return df_libor




def calc_riskfree_libor(df_yields, dt, dte):
	df = df_yields.query('index==@dt')
	
	ON = df.iloc[0]['ON']
	w1 = df.iloc[0]['w1']
	m1 = df.iloc[0]['m1']
	m2= df.iloc[0]['m2']
	m3 = df.iloc[0]['m3']
	m6 = df.iloc[0]['m6']
	m12 = df.iloc[0]['m12']

	years = ([0.0, 1/360, 1/52, 1/12, 2/12, 3/12, 6/12, 12/12])
	rates = ([0.0, ON/100, w1/100, m1/100, m2/100, m3/100, m6/100, m12/100])
	
	df_inter = pd.DataFrame(columns=['0', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12'])
	df_inter.loc[0] = years
	df_inter.loc[1] = rates
	df_inter = df_inter.dropna(axis='columns')
	# print(df_inter)

	f = interpol(df_inter.loc[0], df_inter.loc[1], k=1, bbox=[0.0, 4.0])
	y = float(dte)
	rf = f(y)
	rf = np.round(rf, decimals=4)
	print(dt.strftime('%Y-%m-%d') + " L " + str(dte) + " " + str(rf))
	return rf

