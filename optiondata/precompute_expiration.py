import datetime
import time

import psycopg2
from psycopg2 import extras
from py_vollib.black_scholes import implied_volatility
from py_vollib.black_scholes import black_scholes
from datetime import date, datetime, timedelta



from private import settings
from util import util

def intrinsic(underlying_mid_1545_exp, strike, flag): 
    if flag=='c':
        return max(0, underlying_mid_1545_exp - strike)
    else:
        return max(0, strike - underlying_mid_1545_exp)


def precompute(table, computedate, underlying, include_riskfree):
    
    start = time.time()
        
    db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
    
    underlying_fragment = ""
    if (underlying != "*"): 
        underlying_fragment = "underlying_symbol = '" + underlying + "'"
        
    date_fragment = ""
    if (computedate != "*"): 
        date_fragment = "quote_date = '" + str(computedate) + "'"
        
    query = "SELECT id, quote_date, underlying_mid_1545, mid_1545, expiration, strike, option_type FROM " + table + " WHERE " + underlying_fragment + " AND " + date_fragment 
    
    
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
            
            if expiration < date.today(): 
                
                query = "SELECT underlying_mid_1545 FROM " + table + " WHERE " + underlying_fragment + " AND quote_date = '" + str(expiration) + "' LIMIT 1"
        
                cur2.execute(query)
                underlying_mid_1545_exp = float(cur2.fetchone()[0])
        
                intrinsic_value = intrinsic(underlying_mid_1545_exp, strike, option_type)
                
                print ("gezahlt: " + str(mid_1545))
                print ("uebrig: " + str(intrinsic_value))
                print ()
                
#             bulkrows.append({'bs_price_bid_ask': bs_price_bid_ask, 'rowid': rowid}) 
                        
#         try: 
#             psycopg2.extras.execute_batch(cur2, """UPDATE """ + table + """ SET bs_price_bid_ask=%(bs_price_bid_ask)s WHERE id=%(rowid)s""", bulkrows, page_size=100)
#             db.commit()
#             
#         except Exception as e: 
#             print("an exception occurred")
#             print(e)
#             print (query)
    
        end = time.time() 
        print (end - start)
        print ()
                    
        db.close()
    
# precompute("optiondata", "2020-03-03", "^VIX", True)

