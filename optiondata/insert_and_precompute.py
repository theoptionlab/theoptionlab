#!/usr/bin/python
from private import settings
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os 
import psycopg2 
from util import util
from datetime import datetime 
from optiondata import precompute_greeks
from optiondata import precompute_bs_price

pd.options.mode.chained_assignment = None


startdates = {
  "^RUT": datetime(2004, 1, 2).date(),
  "^SPX": datetime(2004, 1, 2).date(),
  "^VIX": datetime(2006, 2, 27).date(),
  "SPLV": datetime(2011, 11, 1).date(), 
  "SPHB": datetime(2013, 7, 24).date(),
  "VXX": datetime(2010, 5, 28).date()
}

def insert(underlyings, dir, precompute):
    
    print("insert: " + str(underlyings)) 
    print()
    
    engine = create_engine("postgresql://" + settings.db_username + ":" + settings.db_password + "@127.0.0.1/optiondata")
    table = 'optiondata'    

    db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
            
    counter = 0 
    dates = set() 

    
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(dir):
        
        for file in files:
            
            if file.endswith(".zip"): 
    
                index = file.index('_') + 1
                datestring = file[index : (index + 10)]
                
                date = datetime.strptime(datestring, '%Y-%m-%d').date()
                print (date)

                
                unzippedpath = "" 
                
                for underlying in underlyings: 
                    
                    if ((underlying in startdates) and (date > startdates[underlying])) or (underlying not in startdates): 
                                                    
                        query = "SELECT EXISTS(SELECT 1 FROM optiondata WHERE quote_date = '" + datestring + "' AND underlying_symbol = '" + underlying + "')"
                        cur2.execute(query)
                        row = cur2.fetchone()
                                            
                        if (row[0] == False):
    
                            counter += 1
                            print (str(counter) + "\t" + datestring + "\t" + underlying + "\t" + str(file)) 
                                                
                            if unzippedpath == "":
                                datafilepath = root + "/" + file
                                unzippedpath = util.unzip(datafilepath)
                            
                            if unzippedpath is not None: 

                                df = pd.read_csv(unzippedpath, header=0, dtype={"underlying_symbol": object, "quote_date": object, "root": object, "expiration": object, "strike": np.float64, "option_type": object, "open": np.float64, "high": np.float64, "low": np.float64, "close": np.float64, "trade_volume": np.int64, "bid_size_1545": np.int64, "bid_1545": np.float64, "ask_size_1545": np.int64, "ask_1545": np.float64, "underlying_bid_1545": np.float64, "underlying_ask_1545": np.float64, "bid_size_eod": np.int64, "bid_eod": np.float64, "ask_size_eod": np.int64, "ask_eod": np.float64, "underlying_bid_eod": np.float64, "underlying_ask_eod": np.float64, "vwap": object, "open_interest": np.float64, "delivery_code": object})                                    
                                
                                filtered = df[(df['underlying_symbol'] == underlying)]
                                
                                if underlying == "^SPX": 
                                    filtered = filtered[(filtered.root != 'BSZ') & (filtered.root != 'BSK') ]  # filter out binary options                    
                                
                                filtered['option_type'] = filtered.option_type.str.lower()
                                filtered['mid_1545'] = (filtered['bid_1545'] + filtered['ask_1545']) / 2 
                                filtered['underlying_mid_1545'] = (filtered['underlying_bid_1545'] + filtered['underlying_ask_1545']) / 2 
                                
                                if len(filtered.index) > 0:
                                    print (str(len(filtered.index)))
                                    dates.add(datestring)
                                    filtered.to_sql(table, engine, if_exists='append', index=False, chunksize=1000)
                                    db.commit()
                
                
                # only if data hast been inserted, for all underlyings together 
                if precompute:              
                    precompute_bs_price.precompute("optiondata", date, "*", True)
                    precompute_greeks.precompute("optiondata", date, "*", True)
                    
                    
                if ((unzippedpath != "") and (unzippedpath is not None)): 
                    os.remove(unzippedpath)
      
    print ("Done inserting data \n")
    
    db.close()
    return dates
    
