import datetime
import time

import os 
import psycopg2
from psycopg2 import extras
from py_vollib.black_scholes import black_scholes
from py_vollib.black_scholes import implied_volatility
from py_vollib.black_scholes.greeks import analytical 

from private import settings
from util import util


def precompute(table, computedate, underlying, include_riskfree):
    
    start = time.time()
        
    db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
    
    underlying_fragment = ""
    if (underlying != "*"): 
        underlying_fragment = "underlying_symbol = '" + underlying + "' AND "
        
    date_fragment = ""
    if (computedate != "*"): 
        date_fragment = "quote_date = '" + str(computedate) + "' AND "
        
    query = "SELECT id, quote_date, underlying_mid_1545, mid_1545, expiration, strike, option_type FROM " + table + " WHERE " + underlying_fragment + date_fragment + "iv IS NULL" 
    print (query)
    
    cur2.execute(query)
    result = cur2.fetchall()
    
    print (str(computedate) + " " + str(underlying) + ": " + str(len(result)) + " results")
    
    bulkrows = []
    if (len(result) > 0): 
        for row in result:
            
            rowid = row[0]
            quote_date = row[1]
            underlying_mid_1545 = float(row[2])
            mid_1545 = float(row[3])
            expiration = row[4]
            strike = float(row[5])
            option_type = row[6]
            
            expiration_time = datetime.datetime.combine(expiration, datetime.time(16, 0))
            remaining_time_in_years = util.remaining_time(quote_date, expiration_time)
            
            rf = util.interest
            if include_riskfree: 
                rf = util.get_riskfree_libor(quote_date, remaining_time_in_years)
                
            try: iv = implied_volatility.implied_volatility(mid_1545, underlying_mid_1545, int(strike), remaining_time_in_years, rf, option_type)
            except: iv = 0.001
            
            try: bs_price_bid_ask = black_scholes(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv)
            except: bs_price_bid_ask = 0.001
                            
            try: delta = analytical.delta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100
            except: delta = 0.001 
                
            try: theta = analytical.theta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100 
            except: theta = 0.001 
                
            try: vega = analytical.vega(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100
            except: vega = 0.001 
    
            bulkrows.append({'iv': iv, 'bs_price_bid_ask': bs_price_bid_ask, 'delta': delta, 'theta': theta, 'vega': vega, 'rowid': rowid}) 
    
        psycopg2.extras.execute_batch(cur2, """UPDATE """ + table + """ SET iv=%(iv)s, bs_price_bid_ask=%(bs_price_bid_ask)s, delta=%(delta)s, theta=%(theta)s, vega=%(vega)s WHERE id=%(rowid)s""", bulkrows, page_size=100)
        db.commit()
    
        end = time.time() 
        print (end - start)
        print ()
                    
        db.close()
    

# bulk computation 
# for root, dirs, files in os.walk(settings.data_dir):
#     for file in files:
#         if file.endswith(".zip"): 
#               
#             index = file.index('_') + 1
#             datestring = file[index : (index + 10)]
#             precompute("optiondata", datestring, "*", True)


