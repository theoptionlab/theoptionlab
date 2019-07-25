import pandas as pd
import numpy as np 
from scipy.interpolate import InterpolatedUnivariateSpline as interpol
from datetime import datetime

# source = http://iborate.com/usd-libor/
# Libor rates 


def create_libor():
	df_libor = pd.read_csv("LIBOR_USD.csv")
	cols = ['date', 'ON', 'w1', 'w2', 'm1', 'm3', 'm6', 'm9', 'm12']
	df_libor.columns = cols
	df_libor['date'] = pd.to_datetime(df_libor['date'], dayfirst=True)
	df_libor = df_libor.set_index(['date'])
	cols_wo = ['ON', 'w1', 'w2', 'm1', 'm3', 'm6', 'm9', 'm12']
	df_libor[cols_wo] = df_libor[cols_wo].round(2)

	# add missing dates with ffill
	idx = pd.date_range('2000-01-01', '2019-02-04')
	df_libor = df_libor.reindex(idx, method="ffill")
	print (df_libor)
	return df_libor

	# store df_libor in csv
	# df_libor.to_csv("libor_full.csv")
	# print('df_libor stored to csv....')


def calc_riskfree_libor(df_yields, dt, dte):
	print (dt)
	df = df_yields.query('date==@dt')
	# print(df.iloc[0])
	ON = df.iloc[0]['ON']
	w1 = df.iloc[0]['w1']
	w2 = df.iloc[0]['w2']
	m1 = df.iloc[0]['m1']
	m3 = df.iloc[0]['m3']
	m6 = df.iloc[0]['m6']
	m9 = df.iloc[0]['m9']
	m12 = df.iloc[0]['m12']

	years = ([0.0, 1 / 360, 1 / 52, 2 / 52, 1 / 12, 3 / 12, 6 / 12, 9 / 12, 12 / 12])
	rates = ([0.0, ON / 100, w1 / 100, w2 / 100, m1 / 100, m3 / 100, m6 / 100, m9 / 100, m12 / 100])
	df_inter = pd.DataFrame(columns=['0', 'ON', 'w1', 'w2', 'm1', 'm3', 'm6', 'm9', 'm12'])
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

