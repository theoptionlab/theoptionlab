import os  
import psycopg2

from private import settings
from util import util 


def insert(date):

    datafilepath = settings.path_to_data_directory + "UnderlyingOptionsEODQuotes_" + date + ".zip"
    unzippedpath = util.unzip(datafilepath)
    
    conn = psycopg2.connect("host=localhost dbname=optiondata user=" + settings.db_username)
    
    cur = conn.cursor()
    
    print("drop table")
    cur.execute("DROP TABLE fullday")
    
    print("create table")
    cur.execute("CREATE TABLE fullday(underlying_symbol VARCHAR, quote_date date, root VARCHAR, expiration date, strike real, option_type VARCHAR, open real, high real, low real, close real, trade_volume int, bid_size_1545 VARCHAR, bid_1545 real, ask_size_1545 VARCHAR, ask_1545 real, underlying_bid_1545 real, underlying_ask_1545 real, bid_size_eod VARCHAR, bid_eod VARCHAR, ask_size_eod VARCHAR, ask_eod VARCHAR, underlying_bid_eod VARCHAR, underlying_ask_eod VARCHAR, vwap VARCHAR, open_interest VARCHAR, delivery_code VARCHAR)")
    
    print("create indices - important!")
    cur.execute("CREATE INDEX idx_underlying_symbol ON fullday USING btree (underlying_symbol)")
    cur.execute("CREATE INDEX idx_strike ON fullday USING btree (strike)")
    cur.execute("CREATE INDEX idx_expiration ON fullday USING btree (expiration)")
    cur.execute("CREATE INDEX idx_type ON fullday USING btree (option_type)")
    cur.execute("CREATE INDEX idx_bid_1545 ON fullday USING btree (bid_1545)")
    cur.execute("CREATE INDEX idx_ask_1545 ON fullday USING btree (ask_1545)")
    
    print ("copy data")
    with open(unzippedpath, 'r') as f:
        next(f)  # Skip the header row.
        cur.copy_from(f, 'fullday', sep=',')
        conn.commit()
    
    print("create and update columns underlying_mid_1545 and mid_1545")
    cur.execute("ALTER TABLE fullday ADD underlying_mid_1545 real")
    cur.execute("ALTER TABLE fullday ADD mid_1545 real")
    cur.execute("UPDATE fullday SET underlying_mid_1545 = (underlying_bid_1545 + underlying_ask_1545) / 2")
    cur.execute("UPDATE fullday SET mid_1545 = (bid_1545 + ask_1545) / 2")
    
    conn.commit()
    
    cur.execute("SELECT * FROM fullday LIMIT 100")
    print(cur.fetchall())
    
    if unzippedpath != "": 
        os.remove(unzippedpath)
    
    print("done")


date = "2019-11-13"
insert(date)
