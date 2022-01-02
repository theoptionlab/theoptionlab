from optiondata import load_and_precompute
from private import download_data
from private import settings


download_data.download(settings.data_dir)

symbols = ["^RUT", "^VIX"]
precompute = True

# load all data from the directory specified in the path.
dates = load_and_precompute.load(symbols, settings.data_dir, precompute)
print(dates)
print()


# for date in dates:
#     precompute_bs_price.precompute("optiondata", date, "*", True)
#     precompute_greeks.precompute("optiondata", date, "*", True)
#

# if len(dates) > 1:
#     print ("reindex")
#     util.connector.reindex("optiondata")
#     print ("done")
