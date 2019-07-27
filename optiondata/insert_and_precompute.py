from optiondata import insert_data 
from optiondata import precompute_greeks

# will insert all data from the folder stated in the settings.path_to_data_folder 
# symbols = ["^RUT", "^SPX"]
symbols = ["^RUT"]

# insert_data.insert(symbols)

for symbol in symbols: 
    precompute_greeks.precompute(symbol, True)
