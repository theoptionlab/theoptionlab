from optiondata import insert_data 

from optiondata import precompute_greeks
from datetime import timedelta, datetime 

# symbols = ["^RUT"]

# insert all data from the directory specified in the settings.path_to_data_directory 
# insert_data.insert(symbols)


start = datetime(2019, 10, 20).date()
max_date = datetime(2019, 12, 20).date()
current_date = start

while (current_date <= max_date): 
    current_date = current_date + timedelta(days=1)
    precompute_greeks.precompute("optiondata", current_date, "^RUT", True)
    
