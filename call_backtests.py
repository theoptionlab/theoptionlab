# -*- coding: utf-8 -*-
from datetime import datetime 
import time

from strategies import netzero, the_bull, bf70
import backtest_strategies


start_time = time.time()
printalot = True

start = datetime(2006, 11, 1).date()
end = datetime(2021, 4, 1).date()

frequency_string = None 
quantity = None 

backtest_strategies.backtest(bf70.bf70(), "^RUT", "bf70", 100000, quantity, printalot, start, end, bf70.parameters, frequency_string)
backtest_strategies.backtest(the_bull.bull(), "^RUT", "the_bull", 100000, quantity, printalot, start, end, the_bull.parameters, frequency_string)
backtest_strategies.backtest(netzero.netzero(), "^RUT", "netzero", 100000, quantity, printalot, start, end, netzero.parameters, frequency_string)

print()
print("--- %s seconds ---" % (time.time() - start_time))
