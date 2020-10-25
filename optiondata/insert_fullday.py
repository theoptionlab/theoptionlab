import os  
import psycopg2

import time
from private import settings
from util import util 
from datetime import datetime 


def insert(date):
    start = time.time()
    datafilepath = settings.data_dir + "UnderlyingOptionsEODQuotes_" + str(date) + ".zip"
    unzippedpath = util.unzip(datafilepath)
    
    db = psycopg2.connect("host=localhost dbname=optiondata user=" + settings.db_username)
    
    cur = db.cursor()
    
    print("DROP TABLE")
    cur.execute("DROP TABLE IF EXISTS fullday") 
    
    print("CREATE TABLE")
    cur.execute("CREATE TABLE fullday(id SERIAL PRIMARY KEY NOT NULL, underlying_symbol VARCHAR, quote_date date, root VARCHAR, expiration date, strike decimal, option_type VARCHAR, open decimal, high decimal, low decimal, close decimal, trade_volume int, bid_size_1545 VARCHAR, bid_1545 decimal, ask_size_1545 VARCHAR, ask_1545 decimal, underlying_bid_1545 decimal, underlying_ask_1545 decimal, underlying_mid_1545 decimal, bid_size_eod VARCHAR, bid_eod VARCHAR, ask_size_eod VARCHAR, ask_eod VARCHAR, mid_1545 decimal, underlying_bid_eod VARCHAR, underlying_ask_eod VARCHAR, vwap VARCHAR, open_interest VARCHAR, delivery_code VARCHAR, rf decimal, rtiy decimal, iv decimal, bs_price_bid_ask decimal, delta decimal, theta decimal, vega decimal)")

    print("CREATE INDEX...")
    cur.execute("CREATE INDEX idx_underlying_symbol_fullday ON fullday USING btree (underlying_symbol)")
    cur.execute("CREATE INDEX idx_strike_fullday ON fullday USING btree (strike)")
    cur.execute("CREATE INDEX idx_expiration_fullday ON fullday USING btree (expiration)")
    cur.execute("CREATE INDEX idx_type_fullday ON fullday USING btree (option_type)")
    cur.execute("CREATE INDEX idx_bid_1545_fullday ON fullday USING btree (bid_1545)")
    cur.execute("CREATE INDEX idx_ask_1545_fullday ON fullday USING btree (ask_1545)")
    
    print ("copy_from and commit")
    with open(unzippedpath, 'r') as f:
        next(f)  # Skip the header row.
        cur.copy_from(f, 'fullday', sep=',', columns=('underlying_symbol', 'quote_date', 'root', 'expiration', 'strike', 'option_type', 'open', 'high', 'low', 'close', 'trade_volume', 'bid_size_1545', 'bid_1545', 'ask_size_1545', 'ask_1545', 'underlying_bid_1545', 'underlying_ask_1545', 'bid_size_eod', 'bid_eod', 'ask_size_eod', 'ask_eod', 'underlying_bid_eod', 'underlying_ask_eod', 'vwap', 'open_interest', 'delivery_code'))
        db.commit()

    print("Update: LOWER(option_type)")
    cur.execute("UPDATE fullday SET option_type = LOWER(option_type)")
    db.commit()
    
    print("Update: underlying_mid_1545")
    cur.execute("UPDATE fullday SET underlying_mid_1545 = (underlying_bid_1545 + underlying_ask_1545) / 2")
    db.commit()
    
    print("Update: mid_1545")
    cur.execute("UPDATE fullday SET mid_1545 = (bid_1545 + ask_1545) / 2")
    db.commit()
    
    print()
    print ("Done!")


    if unzippedpath != "": 
        os.remove(unzippedpath)

    end = time.time() 
    print (end - start)
    db.close()

date = datetime(2020, 10, 20).date()
insert(date)
