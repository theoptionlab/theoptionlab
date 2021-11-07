# -*- coding: utf-8 -*-
from datetime import datetime 
import time

from strategies import netzero, the_bull, bf70
import backtest_strategies
import compute_stats

start_time = time.time()
start = datetime(2006, 11, 1).date()
end = datetime(2021, 10, 1).date()

frequency_string = 'm'
quantity = None
risk_capital = 100000
include_underlying = True 
underlying = "^RUT"

strategy_name = 'bf70_' + underlying.replace('^','').lower() + '_' + frequency_string
if quantity is not None: 
    strategy_name += "_q" + str(quantity)

backtest_strategies.backtest(bf70.bf70(), underlying, strategy_name, risk_capital, quantity, start, end, bf70.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(strategy_name, underlying, risk_capital)

strategy_name = 'the_bull_' + underlying.replace('^','').lower() + '_' + frequency_string
if quantity is not None: 
    strategy_name += "_q" + str(quantity)

backtest_strategies.backtest(the_bull.bull(), underlying, strategy_name, risk_capital, quantity, start, end, the_bull.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(strategy_name, underlying, risk_capital)

strategy_name = 'netzero_' + underlying.replace('^','').lower() + '_' + frequency_string
if quantity is not None: 
    strategy_name += "_q" + str(quantity)

backtest_strategies.backtest(netzero.netzero(), underlying, strategy_name, risk_capital, quantity, start, end, netzero.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(strategy_name, underlying, risk_capital)

print()
print("--- %s seconds ---" % (time.time() - start_time))
