import insert_data 
import precompute_greeks

# will insert all data from the folder stated in the settings.path_to_data_folder 
symbols = ["^RUT", "^SPX"]

for symbol in symbols: 
    
    insert_data.insert(symbol)
    precompute_greeks.precompute(symbol)
