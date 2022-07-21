# -*- coding: utf-8 -*-
from datetime import datetime
import time
from strategies import netzero, the_bull, bf70
import backtest_strategies
import compute_stats as cs
import pandas as pd
import os
from util import util, underlying_util
import shutil

start_time = time.time()

results_path = os.getcwd() + '/results/'

start = datetime(2006, 11, 1).date()
new_start = datetime(2018, 1, 1).date()
end = datetime(2022, 6, 30).date()

frequency_string = 'm'
quantity = None
risk_capital = 100000
include_underlying = True
underlying = "^RUT"
path = os.getcwd()


def concat_strategy_name(strategy, date):
  strategy_name = strategy + '_' + \
      underlying.replace('^', '').lower() + '_' + frequency_string
  if quantity is not None:
    strategy_name += "_q" + str(quantity)
  strategy_name += "_" + str(date)
  return strategy_name


def backtest(strategy_name):

  strategy = strategy_name.split('_', 1)[0]
  print(strategy)

  if strategy == 'netzero':
    backtest_strategies.backtest(netzero.netzero(), underlying, strategy_name, risk_capital,
                                 quantity, start, end, netzero.parameters, frequency_string)

  if strategy == 'the-bull':
    backtest_strategies.backtest(the_bull.bull(), underlying, strategy_name, risk_capital,
                                 quantity, start, end, the_bull.parameters, frequency_string)

  if strategy == 'bf70':
    backtest_strategies.backtest(bf70.bf70(), underlying, strategy_name, risk_capital,
                                 quantity, start, end, bf70.parameters, frequency_string)


def compute_underlying(strategy_name):
  print("Add underlying")
  underlying_util.add_underlying(
      start, end, underlying, risk_capital, strategy_name)


def compute_stats(strategy_name):
  cs.compute_stats(
      strategy_name, underlying, risk_capital, [])


def copy_files(strategy):

  original_name = concat_strategy_name(strategy, start)
  original_strategy_path = results_path + original_name
  single_results_original = results_path + original_name + '/single_results.csv'

  new_name = concat_strategy_name(strategy, new_start)
  new_strategy_path = results_path + new_name
  util.make_dir(new_strategy_path)
  single_results_new = new_strategy_path + '/single_results.csv'
  shutil.copyfile(single_results_original, single_results_new)

  single_results_df = pd.read_csv(single_results_new)
  for strategy_code in single_results_df.strategy_code.unique():

    original_strategy_code_path = original_strategy_path + \
        '/daily_pnls/' + strategy_code + '/'
    new_strategy_dailies_path = new_strategy_path + \
        '/daily_pnls/'
    util.make_dir(new_strategy_dailies_path)
    new_strategy_code_path = new_strategy_dailies_path + strategy_code + '/'
    util.make_dir(new_strategy_code_path)

    for filename in os.listdir(original_strategy_code_path):
      if filename.endswith('.csv'):

        daily_pnls = pd.read_csv(
            original_strategy_code_path + filename, parse_dates=['date'], index_col=['date'])

        if (daily_pnls.index[0].date() >= new_start):
          shutil.copyfile(original_strategy_code_path + filename,
                          new_strategy_code_path + filename)


def run_and_compute(strategy):
  strategy_name = concat_strategy_name(strategy, start)
  backtest(strategy_name)
  if include_underlying:
    compute_underlying(strategy_name)
  compute_stats(strategy_name)


def derive_shorter_stats(strategy):
  copy_files(strategy)
  new_name = concat_strategy_name(strategy, new_start)
  if include_underlying:
    underlying_util.add_underlying(new_start, end, underlying,
                                   risk_capital, new_name)
  cs.compute_stats(
      new_name, underlying, risk_capital, [], new_start)


for strategy in ('the-bull', 'netzero', 'bf70'):
  run_and_compute(strategy)
  derive_shorter_stats(strategy)

print()
print("--- %s seconds ---" % (time.time() - start_time))
print()
