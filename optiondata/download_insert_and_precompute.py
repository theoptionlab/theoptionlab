from optiondata import insert_data 
from private import settings
from optiondata import precompute_greeks
from optiondata import precompute_bs_price

from datetime import timedelta, datetime 
from private import download_data

download_data.download(settings.data_dir) 


symbols = ["^RUT", "^SPX", "^VIX", "SPLV", "SPHB"]


# insert all data from the directory specified in the path. 
dates = insert_data.insert(symbols, settings.data_dir)
print (dates)
 
for date in dates: 
    precompute_bs_price.precompute("optiondata", date, "*", True)
    precompute_greeks.precompute("optiondata", date, "*", True)

