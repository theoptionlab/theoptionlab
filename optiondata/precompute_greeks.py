import pgdb 
from datetime import datetime, time
from py_vollib.black_scholes import implied_volatility
from py_vollib.black_scholes.greeks import analytical 
from util import util
from private import settings
import pandas as pd
import numpy as np 
from scipy.interpolate import InterpolatedUnivariateSpline as interpol


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
    return rf


def precompute(underlying, include_riskfree):
    
    rf = util.interest
    
    if include_riskfree: 
        df_yields = pd.read_csv("libor/libor_full.csv")
        cols = ['date', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
        df_yields.columns = cols
        df_yields['date'] = pd.to_datetime(df_yields['date'])
        df_yields.set_index('date',inplace=True)
        
        
    print("precompute: " + str(underlying))
    print 
    
    db = pgdb.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
    
    query = "SELECT id, quote_date, underlying_bid_1545, underlying_ask_1545, bid_1545, ask_1545, expiration, strike, option_type FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND iv IS NULL ORDER BY id asc" 
    cur2.execute(query)
    result = cur2.fetchall()
    print(str(len(result)) + " items to precompute")
            
    for row in result:
        rowid = row[0]
        quote_date = row[1]
        underlying_bid_1545 = row[2]
        underlying_ask_1545 = row[3]
        bid_1545 = row[4]
        ask_1545 = row[5]
        expiration = row[6]
        strike = float(row[7])
        option_type = row[8].lower()
        current_quote = float((underlying_bid_1545 + underlying_ask_1545) / 2)
        midprice = float((bid_1545 + ask_1545) / 2)
        
        expiration_time = datetime.combine(expiration, time(16, 0))
        remaining_time_in_years = util.remaining_time(quote_date, expiration_time)
        
        if include_riskfree: 
            rf = calc_riskfree_libor(df_yields, quote_date, remaining_time_in_years)
            
        delta = 0.001 
        theta = 0.001 
        vega = 0.001 
        
        if remaining_time_in_years > 0: 
            
            try:
                iv = implied_volatility.implied_volatility(midprice, current_quote, int(strike), remaining_time_in_years, rf, option_type)
            except: 
                iv = 0.001
                
            delta = analytical.delta(option_type, current_quote, strike, remaining_time_in_years, util.interest, iv) * 100
            theta = analytical.theta(option_type, current_quote, strike, remaining_time_in_years, util.interest, iv) * 100 
            vega = analytical.vega(option_type, current_quote, strike, remaining_time_in_years, util.interest, iv) * 100 
        
        updateQuery = "UPDATE optiondata SET iv=%s, delta=%s, theta=%s, vega=%s WHERE id=%s" % (iv, delta, theta, vega, rowid)
        try: 
            cur2.execute(updateQuery)
            db.commit()
        except: 
            print("Except")
            print(rowid)
            print(current_quote)
            print(midprice)
            print(iv)
            print(delta)
            print(theta)
            print(vega)
            print(updateQuery)
    
    db.close()