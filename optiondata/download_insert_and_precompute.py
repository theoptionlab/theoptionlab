from optiondata import insert_data 
from private import settings
from optiondata import precompute_greeks
from datetime import timedelta, datetime 
from private import download_data

download_data.download() 

symbols = ["^RUT", "^SPX"]

# insert all data from the directory specified in the path. 
# settings.path_to_data_directory for current dir and settings.data_directory for entire data dir
insert_data.insert(symbols, settings.path_to_data_directory)


start = datetime(2019, 12, 31).date()
max_date = datetime(2020, 1, 15).date()
current_date = start

while (current_date <= max_date): 
    current_date = current_date + timedelta(days=1)
    precompute_greeks.precompute("optiondata", current_date, "*", True)
     
