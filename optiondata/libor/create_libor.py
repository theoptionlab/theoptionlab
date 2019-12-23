import pandas as pd

# libor rates from http://iborate.com/usd-libor/
df_libor = pd.read_csv("LIBOR_USD.csv")
cols = ['date', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
df_libor.columns = cols
df_libor['date'] = pd.to_datetime(df_libor['date'])
df_libor.set_index('date', inplace=True)
cols_wo = ['ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
df_libor[cols_wo] = df_libor[cols_wo].round(2)

# add missing dates with ffill
df_libor = df_libor.sort_index()
idx = pd.date_range('2004-01-01', '2019-12-31')
df_libor = df_libor.reindex(idx, method="ffill")

# store df_libor in csv
df_libor.to_csv("libor_full.csv")
print('df_libor stored to libor_full.csv')
