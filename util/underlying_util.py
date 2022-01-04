# -*- coding: utf-8 -*-
from __future__ import division
import os
from util import util
from datetime import datetime
from datetime import timedelta
import pandas as pd
import trading_calendars as tc
import pytz
xnys = tc.get_calendar("XNYS")

cwd = os.getcwd()


def add_underlying(start, end, underlying, risk_capital, strategy_name):
  # create results file and trade log entry for underlying
  underlying_daily_pnls_dict = {}
  underlying_date = start
  underlying_multiplier = None
  underlying_at_entry = None
  entry_vix = None
  previouspnl = 0

  while (underlying_date <= end):

    while ((xnys.is_session(pd.Timestamp(underlying_date, tz=pytz.UTC)) is False)
            or (util.connector.query_midprice_underlying(underlying, underlying_date) is None)):

      underlying_date = underlying_date + timedelta(days=1)
      if (underlying_date >= end) or (underlying_date >= datetime.now().date()):
        break

    underlying_midprice = util.connector.query_midprice_underlying(
        underlying, underlying_date)

    if underlying_midprice != 0:

      if underlying_multiplier is None:
        underlying_start_date = underlying_date
        underlying_at_entry = underlying_midprice
        underlying_multiplier = (risk_capital / underlying_midprice)
        entry_vix = util.connector.query_midprice_underlying(
            "^VIX", underlying_date)

      current_pnl = (underlying_multiplier *
                     underlying_midprice) - risk_capital
      if current_pnl != None:
        underlying_daily_pnls_dict[underlying_date] = format(
            float(current_pnl - previouspnl), '.2f')
        previouspnl = current_pnl

    underlying_date = underlying_date + timedelta(days=1)

  # save results
  underlying_daily_pnls = pd.DataFrame.from_dict(
      underlying_daily_pnls_dict, orient='index')
  underlying_daily_pnls = underlying_daily_pnls.reindex(
      underlying_daily_pnls.index.rename('date'))
  underlying_daily_pnls.index = pd.to_datetime(underlying_daily_pnls.index)
  underlying_daily_pnls.sort_index(inplace=True)
  underlying_daily_pnls.columns = ['pnl']

  underlying_strategy_code_path = cwd + '/results/' + strategy_name + \
      '/daily_pnls/' + str(underlying.replace("^", "")) + "/"

  util.make_dir(underlying_strategy_code_path)
  underlying_file_name = underlying_strategy_code_path + 'underlying.csv'
  underlying_daily_pnls.to_csv(underlying_file_name)

  # add to single_results
  single_results_file = cwd + '/results/' + strategy_name + '/single_results.csv'
  single_results_df = pd.read_csv(
      single_results_file, parse_dates=['entry_date'], index_col=0)

  # if row exists delete it
  if single_results_df.tail(1)['strategy_code'].values[0] == "RUT":
    single_results_df.drop(single_results_df.tail(1).index, inplace=True)

# save underlying to trade_log
  trade_log = dict({'trade nr.': 0, 'strategy_code': str(underlying.replace("^", "")), 'entry_date': start, 'expiration': None, 'exit_date': underlying_date, 'entry_underlying': str(format(float(underlying_at_entry), '.2f')), 'entry_vix': entry_vix, 'strikes': None, 'iv_legs': None, 'entry_price': str(format(
      float(risk_capital), '.2f')), 'dte': 0, 'dit': (end - start).days, 'pnl': str(format(float(current_pnl), '.2f')), 'dailypnls': None, 'max_risk': str(format(float(risk_capital), '.2f')), 'position_size': underlying_multiplier, 'percentage': str(format(float(round((float(current_pnl) / risk_capital) * 100, 2)), '.2f')) + '%', 'exit': None})
  single_results_df = single_results_df.append(trade_log, ignore_index=True)
  single_results_df.to_csv(single_results_file)
