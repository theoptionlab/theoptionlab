import pandas
import numpy as np
from sqlalchemy import create_engine
from private import settings
import pgdb 

# idea to use unzip function from util

engine = create_engine("postgresql://" + settings.db_username + ":" + settings.db_password + "@127.0.0.1/optiondata")
table = 'fullday'

db = pgdb.connect(host="localhost", user=settings.db_username, password=settings.db_password, database="optiondata") 
cur2 = db.cursor()

reader = pandas.read_csv(settings.path_to_csv, chunksize=10000, header=0, dtype={"underlying_symbol": object, "quote_date": object, "root": object, "expiration": object, "strike": np.float64, "option_type": object, "open": np.float64, "high": np.float64, "low": np.float64, "close": np.float64, "trade_volume": np.int64, "bid_size_1545": np.int64, "bid_1545": np.float64, "ask_size_1545": np.int64, "ask_1545": np.float64, "underlying_bid_1545": np.float64, "underlying_ask_1545": np.float64, "bid_size_eod": np.int64, "bid_eod": np.float64, "ask_size_eod": np.int64, "ask_eod": np.float64, "underlying_bid_eod": np.float64, "underlying_ask_eod": np.float64, "vwap": object, "open_interest": np.float64, "ask_eod": np.float64, "delivery_code": object})                
for chunk in reader:
    print(chunk)
    chunk['option_type'] = chunk.option_type.str.lower()
    chunk.to_sql(table, engine, if_exists='append', index=False)

db.commit()
db.close()

print("Done")
print 
