import datetime
import time

import psycopg2
from psycopg2 import extras
from py_vollib.black_scholes import implied_volatility
from py_vollib.black_scholes.greeks import analytical 

from private import settings
from util import util


def precompute(table, date, underlying, include_riskfree):
    
    start = time.time()
        
    db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
    
    if (underlying == "*"): 
        query = "SELECT id, quote_date, underlying_mid_1545, mid_1545, expiration, strike, option_type FROM " + table + " WHERE quote_date = '" + str(date) + "'" 
    else: # OR delta != NULL OR theta != NULL OR vega != NULL
        query = "SELECT id, quote_date, underlying_mid_1545, mid_1545, expiration, strike, option_type FROM " + table + " WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(date) + "' AND iv IS NULL" 
    
    cur2.execute(query)
    result = cur2.fetchall()
    
    print (str(date) + " " + str(underlying) + ": " + str(len(result)) + " results")
    
    bulkrows = []
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
            
        try: delta = analytical.delta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100
        except: delta = 0.001 
            
        try: theta = analytical.theta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100 
        except: theta = 0.001 
            
        try: vega = analytical.vega(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100
        except: vega = 0.001 

        bulkrows.append({'iv': iv, 'delta': delta, 'theta': theta, 'vega': vega, 'rowid': rowid}) 
                    
#     try: 
    psycopg2.extras.execute_batch(cur2, """UPDATE """ + table + """ SET iv=%(iv)s, delta=%(delta)s, theta=%(theta)s, vega=%(vega)s WHERE id=%(rowid)s""", bulkrows, page_size=100)
        # cur2.executemany("""UPDATE """ + table + """ SET iv=%(iv)s, delta=%(delta)s, theta=%(theta)s, vega=%(vega)s WHERE id=%(rowid)s""", bulkrows)
    db.commit()
    print ("committed")
        
#     except Exception as e: 
#         print("an exception occurred")
#         print(e)

    end = time.time() 
    print (end - start)
    print ("Done precomputing")
    
    print ()
                
    db.close()
