from private import settings
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os 
import psycopg2 
from util import util
pd.options.mode.chained_assignment = None

                    
def insert(underlyings):
    
    print("insert: " + str(underlyings)) 
    print()
    
    engine = create_engine("postgresql://" + settings.db_username + ":" + settings.db_password + "@127.0.0.1/optiondata")
    table = 'optiondata'    

    db = psycopg2.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
    cur2 = db.cursor()
            
    counter = 0 
    
    onlyfiles = [f for f in listdir(settings.path_to_data_directory) if isfile(join(settings.path_to_data_directory, f))]
    for datafile in onlyfiles: 
#         print (datafile)

        if datafile.endswith(".zip"): 

            index = datafile.index('_') + 1
            datestring = datafile[index : (index + 10)]
            unzippedpath = "" 
            
            for underlying in underlyings: 
                            
                query = "SELECT EXISTS(SELECT 1 FROM optiondata WHERE quote_date = '" + datestring + "' AND underlying_symbol = '" + underlying + "')"
                cur2.execute(query)
                row = cur2.fetchone()
                
                if (row[0] == 0):
                    
                    counter += 1
                    print (str(counter) + "\t" + datestring + "\t" + underlying + "\t" + str(datafile)) 
                                        
                    if unzippedpath == "":
                        datafilepath = settings.path_to_data_directory + datafile
                        unzippedpath = util.unzip(datafilepath)
                    
                    df = pd.read_csv(unzippedpath, header=0, dtype={"underlying_symbol": object, "quote_date": object, "root": object, "expiration": object, "strike": np.float64, "option_type": object, "open": np.float64, "high": np.float64, "low": np.float64, "close": np.float64, "trade_volume": np.int64, "bid_size_1545": np.int64, "bid_1545": np.float64, "ask_size_1545": np.int64, "ask_1545": np.float64, "underlying_bid_1545": np.float64, "underlying_ask_1545": np.float64, "bid_size_eod": np.int64, "bid_eod": np.float64, "ask_size_eod": np.int64, "ask_eod": np.float64, "underlying_bid_eod": np.float64, "underlying_ask_eod": np.float64, "vwap": object, "open_interest": np.float64, "delivery_code": object})                                    
                    
                    filtered = df[(df['underlying_symbol'] == underlying)]
                    
                    if underlying == "^SPX": 
                        filtered = filtered[(filtered.root != 'BSZ') & (filtered.root != 'BSK') ]  # filter out binary options                    
                    
                    filtered['option_type'] = filtered.option_type.str.lower()
                    filtered['mid_1545'] = (filtered['bid_1545'] + filtered['ask_1545']) / 2 
                    filtered['underlying_mid_1545'] = (filtered['underlying_bid_1545'] + filtered['underlying_ask_1545']) / 2 
                    
                    filtered.to_sql(table, engine, if_exists='append', index=False, chunksize=1000)
#                     filtered.to_sql(table, engine, if_exists='replace', index=False)

                    db.commit()
                    
            if unzippedpath != "": 
                os.remove(unzippedpath)
    
    print ()     
    print ("Done inserting data ")
    print ()
    
    db.close()
    
