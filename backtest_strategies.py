# -*- coding: utf-8 -*-
from __future__ import division

from datetime import datetime
from datetime import timedelta
import itertools
import os
import shutil
import time

import pandas as pd

import run_strategy

from util import util
from util import entries

import trading_calendars as tc
import pytz
xnys = tc.get_calendar("XNYS")


def dict_product(d):
  keys = d.keys()
  for element in itertools.product(*d.values()):
    yield dict(zip(keys, element))


def get_next_entry(index_nr, frequency_string, single_entries, entry_date, end_date, underlying, dte):

  if frequency_string == 'c':
    entries = {}

    while (entry_date <= end_date):

      expiration = util.connector.select_expiration(
          entry_date, underlying, "p", dte)
      if expiration is None:
        entry_date = entry_date + timedelta(days=1)
        continue

      else:
        entries[entry_date] = expiration
        return list(entries.items())[0]

  else:
    if index_nr < len(single_entries):
      return single_entries[index_nr]

  return None


def run_strategies(permutations, strategy_name, parameters, strategy_path, frequency_string, underlying, start, end, strategy, risk_capital, quantity, include_underlying=False):

  trade_log = {}
  i = 0

  for permutation in permutations:

    running = True

    for k, v in permutation.items():
      if util.printalot:
        print(k, v)

    if (strategy_name == 'bf70' or strategy_name == 'bf70_plus') and (permutation['cheap_entry'] == None) and (permutation['down_day_entry'] == False) and (permutation['patient_entry'] == True):
      if util.printalot:
        print('continue')
      continue

    strategy_code = util.derive_strategy_code(permutation, parameters)
    print(strategy_code)

    # make dir for permutation
    strategy_code_path = strategy_path + '/daily_pnls/' + strategy_code + "/"
    util.make_dir(strategy_code_path)

    single_entries = None
    # get entries, measure time
    starttime = time.time()
    if frequency_string == 'c':
      single_entries = {}
    if frequency_string == 'b':
      single_entries = entries.getDailyEntries(
          underlying, start, end, permutation['dte_entry'])
    if frequency_string == 'sms':
      single_entries = entries.getSMSEntries(
          underlying, start, end, permutation['dte_entry'])
    if frequency_string == 'm':
      single_entries = entries.getEntries(
          underlying, start, end, permutation['dte_entry'])
    if single_entries is None:
      print("frequency string not known: " + frequency_string)
      return False

    print('time needed to get entries: ' +
          format(float(time.time() - starttime), '.2f'))

    # loop through entries
    trade_nr = 0
    index_nr = 0
    next_date = None

    while (running):

      if next_date is None:
        next_date = start
      entry = get_next_entry(index_nr, frequency_string, single_entries,
                             next_date, end, underlying, permutation['dte_entry'])

      if entry is not None:
        entrydate = entry[0]
        expiration = entry[1]

        if entrydate >= (datetime.now().date() - timedelta(days=7)):
          break

        if strategy_name.startswith('the_bull'):
          permutation['dte_exit'] = 37
          try:
            next_entry = get_next_entry(
                index_nr + 1, frequency_string, single_entries, next_date, end, underlying, permutation['dte_entry'])
            if next_entry is not None:
              permutation['dte_exit'] = 66 - (next_entry[0] - entrydate).days
          except Exception as e:
            print(e)

        # run with parameters
        strategy.setParameters(permutation)
        if ((strategy_name.startswith('bf70') and (frequency_string == 'c'))):
          strategy.patient_days_before = 0
        result = run_strategy.fly(
            strategy, underlying, risk_capital, quantity, entrydate, expiration)

        if (not result is None):
          trade_nr += 1
          i += 1

          # save dailypnls
          file_name = strategy_code_path + str(i) + '.csv'
          result['dailypnls'].to_csv(file_name)
          del result['dailypnls']

          trade_log[i] = dict(
              {'trade nr.': trade_nr, 'strategy_code': strategy_code}, **result)
          print(trade_log[i])
          next_date = (result["exit_date"]) + timedelta(days=1)

        else:
          next_date = next_date + timedelta(days=1)

        index_nr += 1

      else:
        running = False

  # we used to include the underlying here
  # if (include_underlying):
  #   util.add_underlying()

  # finished looping, save trade_log
  df_log = pd.DataFrame.from_dict(trade_log, orient='index')
  df_log.to_csv(strategy_path + '/single_results.csv')


def backtest(strategy, underlying, strategy_name, risk_capital, quantity, start, end, parameters, frequency_string="m", include_underlying=False):

  if util.printalot:
    print('strategy_name: ' + str(strategy_name))
  if util.printalot:
    print('risk_capital: ' + str(risk_capital))
  if util.printalot:
    print('underlying: ' + str(underlying))
  if util.printalot:
    print('start: ' + str(start))
  if util.printalot:
    print('end: ' + str(end))
  if util.printalot:
    print()

  # prepare
  if util.printalot:
    print('number of combinations: ' + str(len(list(dict_product(parameters)))))
  for permutation in dict_product(parameters):
    print(util.derive_strategy_code(permutation, parameters))
  permutations = dict_product(parameters)

  # create directories
  path = os.getcwd()
  util.make_dir(path + '/results')
  strategy_path = path + '/results/' + strategy_name
  util.make_dir(strategy_path)
  try:
    shutil.rmtree(strategy_path + '/daily_pnls')
  except Exception as e:
    print(e)
  util.make_dir(strategy_path + '/daily_pnls')

  run_strategies(permutations, strategy_name, parameters, strategy_path, frequency_string,
                 underlying, start, end, strategy, risk_capital, quantity, include_underlying)
