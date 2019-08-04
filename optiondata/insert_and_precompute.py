from optiondata import insert_data 
from optiondata import precompute_greeks

# insert all data from the directory specified in the settings.path_to_data_directory 
symbols = ["^RUT", "^SPX"]
insert_data.insert(symbols)

for symbol in symbols: 
    precompute_greeks.precompute(symbol, True)
