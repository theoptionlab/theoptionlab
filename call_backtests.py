# -*- coding: utf-8 -*-
from datetime import datetime 
import time

from strategies import netzero, the_bull, bf70
import backtest_strategies


start_time = time.time()
printalot = True

start = datetime(2006, 11, 1).date()
end = datetime(2021, 1, 1).date()

daily_entry = False 

# backtest_strategies.backtest(bf70.bf70(), "^RUT", "bf70", 100000, printalot, start, end, bf70.parameters, daily_entry)
# backtest_strategies.backtest(the_bull.bull(), "^RUT", "the_bull", 100000, printalot, start, end, the_bull.parameters, daily_entry)
backtest_strategies.backtest(netzero.netzero(), "^RUT", "netzero", 100000, printalot, start, end, netzero.parameters, daily_entry)

print()
print("--- %s seconds ---" % (time.time() - start_time))
