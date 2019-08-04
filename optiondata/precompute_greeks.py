# import pgdb 
import psycopg2
import time
import datetime
from py_vollib.black_scholes import implied_volatility
from py_vollib.black_scholes.greeks import analytical 
from util import util
from private import settings


def precompute(underlying, include_riskfree):
    
    done = False 
    bulksize = 100000
    counter = 0 
        
    print("precompute: " + str(underlying))
    print()
    
    while not done: 
        
        db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
        cur2 = db.cursor()
        
        print ("Query for next " + str(bulksize) + " items to precompute ")
        query = "SELECT id, quote_date, underlying_mid_1545, mid_1545, expiration, strike, option_type FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND iv IS NULL LIMIT " + str(bulksize) 
        cur2.execute(query)
        result = cur2.fetchall()
        print(str(len(result)) + " items to precompute")
        if len(result) == 0: 
            done = True 
            print ("Done precomputing")
            print ()
        
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
                
            try: 
                iv = implied_volatility.implied_volatility(mid_1545, underlying_mid_1545, int(strike), remaining_time_in_years, rf, option_type)
                delta = analytical.delta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100
                theta = analytical.theta(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100 
                vega = analytical.vega(option_type, underlying_mid_1545, strike, remaining_time_in_years, rf, iv) * 100 
            
            except: 
                iv = 0.001
                delta = 0.001 
                theta = 0.001 
                vega = 0.001 
        
            bulkrows.append({'iv': iv, 'delta': delta, 'theta': theta, 'vega': vega, 'rowid': rowid}) 
            counter += 1 
                        
            if (((counter %1000) == 0) or ((len(result) < bulksize) and (counter == len(result)))): 
                try: 
                    cur2.executemany("""UPDATE optiondata SET iv=%(iv)s, delta=%(delta)s, theta=%(theta)s, vega=%(vega)s WHERE id=%(rowid)s""", bulkrows)
                    db.commit()
                    print ("inserted: " + str(counter))
                    bulkrows = []
                    time.sleep(1)
                    
                except Exception as e: 
                    print("an exception occurred")
                    print(e)
                    
            if (len(result) < bulksize) and (counter == len(result)):
                done = True 
                print ("Done precomputing")
                print ()
                
    db.close()