from optiondata import insert_data 

from optiondata import precompute_greeks
from datetime import datetime 

# insert all data from the directory specified in the settings.path_to_data_directory 
symbols = ["^SPX"]
insert_data.insert(symbols)



# precompute_greeks.precompute("fullday", date, "*", True)
