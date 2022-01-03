# -*- coding: utf-8 -*-
from datetime import datetime
import time

from strategies import netzero, the_bull, bf70
import backtest_strategies
import compute_stats

start_time = time.time()
start = datetime(2006, 11, 1).date()
end = datetime(2021, 12, 31).date()

frequency_string = 'm'
quantity = None
risk_capital = 100000
include_underlying = True
underlying = "^RUT"


def concat_strategy_name(strategy):
  strategy_name = strategy + '_' + \
      underlying.replace('^', '').lower() + '_' + frequency_string
  if quantity is not None:
    strategy_name += "_q" + str(quantity)
  return strategy_name


netzero_name = concat_strategy_name('bf70')
backtest_strategies.backtest(bf70.bf70(), underlying, netzero_name, risk_capital,
                             quantity, start, end, bf70.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(
    start, netzero_name, underlying, risk_capital)


the_bull_name = concat_strategy_name('the_bull')
backtest_strategies.backtest(the_bull.bull(), underlying, the_bull_name, risk_capital,
                             quantity, start, end, the_bull.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(
    start, the_bull_name, underlying, risk_capital)


netzero_name = concat_strategy_name('netzero')
backtest_strategies.backtest(netzero.netzero(), underlying, netzero_name, risk_capital,
                             quantity, start, end, netzero.parameters, frequency_string, include_underlying)
compute_stats.compute_stats(
    start, netzero_name, underlying, risk_capital)

print()
print("--- %s seconds ---" % (time.time() - start_time))
