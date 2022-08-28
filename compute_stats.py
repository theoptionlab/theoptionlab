# -*- coding: utf-8 -*-
from __future__ import division

import collections
from datetime import datetime
import os
import shutil

import numpy as np
import pandas as pd

from util import util
from util import performance

import pandas_market_calendars as pmc
xnys = pmc.get_calendar('XNYS')


def compute_stats(strategy_name, underlying, risk_capital, exclude=[], start_date=datetime(2004, 1, 1).date()):

  # start computing stats
  equity_curve = collections.OrderedDict()
  results_table = collections.OrderedDict()
  j = 0

  path = os.getcwd()
  strategy_path = path + '/results/' + strategy_name
  single_results_df = pd.read_csv(
      strategy_path + '/single_results.csv', parse_dates=['entry_date'])
  single_results = single_results_df.to_dict(orient='index')

  for strategy_code in single_results_df.strategy_code.unique():
    print(strategy_code)

    if (strategy_code not in exclude):

      exits = {}
      total_positions = 0
      total_risk = 0
      total_pnl = 0
      winners = 0
      allwinners = 0
      alllosers = 0
      maxwinner = 0
      losers = 0
      maxloser = 0
      total_dit = 0

      total_daily_pnls = None
      total = risk_capital
      running_global_peak = 0
      running_global_peak_date = datetime(2000, 1, 1).date()
      max_dd = 0
      running_max_dd_date = datetime(2000, 1, 1).date()

      # compute stats for strategy
      for key, value in single_results.items():
        entry_date = value['entry_date'].date()

        if ((value['strategy_code'] == strategy_code) and (entry_date >= start_date)):

          total_positions += int(value['position_size'])

          total_risk += value['max_risk']
          total_pnl += value['pnl']
          if value['pnl'] >= 0:
            allwinners += value['pnl']
            winners += 1
            if value['pnl'] > maxwinner:
              maxwinner = value['pnl']

          else:
            alllosers += value['pnl']
            losers += 1
            if value['pnl'] < maxloser:
              maxloser = value['pnl']

          total_dit += value['dit']

          if value['exit'] in exits:
            exits[value['exit']] += 1
          else:
            exits[value['exit']] = 1

      # merge total_daily_pnls per strategy
      number_of_trades = 0

      strategy_code_path = strategy_path + '/daily_pnls/' + strategy_code + '/'
      for filename in os.listdir(strategy_code_path):
        if filename.endswith('.csv'):

          daily_pnls = pd.read_csv(
              strategy_code_path + filename, parse_dates=['date'], index_col=['date'])

          if (daily_pnls.index[0].date() >= start_date):

            number_of_trades += 1

            if (total_daily_pnls is None):
              total_daily_pnls = daily_pnls

            else:
              total_daily_pnls = pd.concat([daily_pnls, total_daily_pnls], axis=0,
                                           join='outer', ignore_index=False).groupby(['date'], as_index=True).sum()
              total_daily_pnls.sort_index(inplace=True)

      if (total_daily_pnls is None):
        print('no trades')
        continue

      total_daily_pnls['cum_sum'] = total_daily_pnls.pnl.cumsum() + total
      total_daily_pnls['daily_ret'] = total_daily_pnls['cum_sum'].pct_change()

      annualized_sharpe_ratio = performance.annualized_sharpe_ratio(
          np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)
      annualized_sortino_ratio = performance.annualized_sortino_ratio(
          np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)

      for key, value in total_daily_pnls.iterrows():
        j += 1
        total += value['pnl']
        equity_curve[j] = {'strategy': strategy_code,
                           'date': key.date(), 'pnl': format(float(total), '.2f')}

        if total >= running_global_peak:
          running_global_peak = total
          min_since_global_peak = total
          running_global_peak_date = key
        if total < min_since_global_peak:
          min_since_global_peak = total
          if total - running_global_peak <= max_dd:
            max_dd = total - running_global_peak
            running_max_dd_date = key
            max_dd_percentage = round((max_dd / running_global_peak * 100), 2)
            max_dd_risk_percentage = round((max_dd / risk_capital * 100), 2)
            max_dd_duration = abs(
                (running_global_peak_date - running_max_dd_date).days)

      average_pnl_trade_dollar = int(total_pnl / number_of_trades)
      average_pnl_day_dollar = int(total_pnl / total_dit)

      average_risk = int(total_risk / number_of_trades)
      average_percentage = round(total_pnl / abs(total_risk) * 100, 2)
      percentage_winners = int((winners / number_of_trades) * 100)
      percentage_losers = int((losers / number_of_trades) * 100)

      try:
        average_winner = int(allwinners / winners)
      except ZeroDivisionError:
        average_winner = 0

      try:
        average_loser = int(alllosers / (number_of_trades - winners))
      except ZeroDivisionError:
        average_loser = 0

      average_dit = int(total_dit / number_of_trades)
      average_position_size = format(
          float(total_positions / number_of_trades), '.2f')
      rod = format(float(average_percentage /
                   (total_dit / number_of_trades)), '.2f')

      days = (equity_curve[j]['date'] - equity_curve[1]['date']).days
      years = round((days / 365), 2)

      annualized_pnl = int(total_pnl) / years

      annualized_RoR = round((annualized_pnl / risk_capital * 100), 2)
      rrr = round((annualized_RoR / -max_dd_risk_percentage), 2)

      annualized_RoR = format(annualized_RoR, '.2f')
      rrr = format(rrr, '.2f')

      total_pnl_percentage = round((total_pnl / risk_capital * 100), 2)

      average_pnl_percentage_trade = round(
          total_pnl_percentage / number_of_trades, 2)
      average_pnl_percentage_trade = (
          '{:,.2f}'.format(average_pnl_percentage_trade))

      average_pnl_percentage_day = round(
          total_pnl_percentage / total_dit, 2)
      average_pnl_percentage_day = (
          '{:,.2f}'.format(average_pnl_percentage_day))

      total_pnl_percentage = ('{:,.2f}'.format(total_pnl_percentage))

      annualized_sharpe_ratio = format(annualized_sharpe_ratio, '.2f')
      annualized_sortino_ratio = format(annualized_sortino_ratio, '.2f')

      max_dd_percentage = format(max_dd_percentage, '.2f')
      average_percentage = format(average_percentage, '.2f')

      total_dit = ('{:,.0f}'.format(total_dit))

      results_table[strategy_code] = {

          # Trade details
          'Trade details': '',
          'avg size': average_position_size,
          'avg risk $': '$' + str('{:,.0f}'.format(average_risk)),
          'avg DIT': average_dit,
          'total DITs': total_dit,

          # P&L $
          'P&L $': '',
          'avg p&l/trade $': '$' + str('{:,.0f}'.format(average_pnl_trade_dollar)),
          'avg p&l/day $': '$' + str('{:,.0f}'.format(average_pnl_day_dollar)),
          'total pnl $': '$' + str('{:,.0f}'.format(total_pnl)),

          # P&L %
          'P&L %': '',
          'avg p&l/trade %': str(average_pnl_percentage_trade) + '%',
          'avg p&l/day %': str(average_pnl_percentage_day) + '%',
          'total pnl %': str(total_pnl_percentage) + '%',

          # RoR and RRR
          'RoR and RRR': '',
          'avg RoR %': str(average_percentage) + '%',
          'ann RoR %': str(annualized_RoR) + '%',
          'avg RoR/DIT': rod,
          'RRR': rrr,

          # Trades
          'Trades': '',
          'total trades': number_of_trades,
          'winners': winners,
          'winners %': str(percentage_winners) + '%',
          'avg winner $': '$' + str('{:,.0f}'.format(average_winner)),
          'max winner $': '$' + str('{:,.0f}'.format(maxwinner)),
          'losers': losers,
          'losers %': str(percentage_losers) + '%',
          'avg loser $': '$' + str('{:,.0f}'.format(average_loser)),
          'max loser $': '$' + str('{:,.0f}'.format(maxloser)),

          # Drawdown
          'Drawdown': '',
          'max dd $': '$' + str('{:,.0f}'.format(max_dd)),
          'max dd on risk %': str(max_dd_risk_percentage) + '%',
          'max dd on prev peak %': str(max_dd_percentage) + '%',
          'max dd date': running_max_dd_date.date(),
          'max dd days': max_dd_duration,

          # Performance
          'Performance': '',
          'Sharpe': annualized_sharpe_ratio,
          'Sortino': annualized_sortino_ratio, }

  # save computed stats
  df_curve = pd.DataFrame.from_dict(equity_curve, orient='index')
  df_curve.to_csv(strategy_path + '/results.csv')

  df_table = pd.DataFrame.from_dict(results_table)
  print(df_table)
  df_table.to_html(strategy_path + '/results_table.html')

  # Copy files for web
  shutil.copyfile(path + '/util/web/d3.js', strategy_path + '/d3.js')
  shutil.copyfile(path + '/util/web/index.html', strategy_path + '/index.html')

  try:
    shutil.copyfile(path + '/util/web/' + str(strategy_name)[0:-11] +
                    '.html', strategy_path + '/strategy.html')
  except Exception as e:
    print(e)
