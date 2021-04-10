# -*- coding: utf-8 -*-
from datetime import datetime 
import time

from strategies import netzero, the_bull, bf70
import backtest_strategies
import compute_stats

start_time = time.time()
start = datetime(2006, 11, 1).date()
end = datetime(2021, 4, 1).date()

frequency_string = None 
quantity = None 
risk_capital = 100000
include_underlying = True 
underlying = "^RUT"

backtest_strategies.backtest(bf70.bf70(), underlying, "bf70", risk_capital, quantity, start, end, bf70.parameters, frequency_string, include_underlying)
compute_stats.compute_stats("bf70", underlying, risk_capital)

backtest_strategies.backtest(the_bull.bull(), underlying, "the_bull", risk_capital, quantity, start, end, the_bull.parameters, frequency_string, include_underlying)
compute_stats.compute_stats("the_bull", underlying, risk_capital)
#
backtest_strategies.backtest(netzero.netzero(), underlying, "netzero", risk_capital, quantity, start, end, netzero.parameters, frequency_string, include_underlying)
compute_stats.compute_stats("netzero", underlying, risk_capital)

print()
print("--- %s seconds ---" % (time.time() - start_time))
