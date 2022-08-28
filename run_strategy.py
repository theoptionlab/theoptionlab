# -*- coding: utf-8 -*-
from __future__ import division
from datetime import timedelta, datetime
import pandas as pd
import pandas_market_calendars as pmc
import pytz

from util import util

xnys = pmc.get_calendar("XNYS")


def checkMinIV(combo, miniv):
  for position in combo.getPositions():
    if position is not None:
      iv = util.connector.select_iv(position.option.entry_date, position.option.underlying,
                                    position.option.expiration, position.option.type, position.option.strike)
      if (iv < miniv):
        print("IV below minimum IV")
        return False
  return True


def fly(strategy, underlying, risk_capital, quantity, entrydate, expiration):

  flying = True
  daily_pnls_dict = {}
  previouspnl = 0
  adjustment_counter = 0
  realized_pnl = 0
  current_date = entrydate
  max_date = current_date
  combo = None

  if strategy.patient_entry:
    current_date = entrydate - timedelta(days=strategy.patient_days_before)
    max_date = entrydate + timedelta(days=strategy.patient_days_after)

  while (current_date <= max_date):

    combo = None

    while ((xnys.is_session(pd.Timestamp(current_date, tz=pytz.UTC)) is False)
           or (util.connector.query_midprice_underlying(underlying, current_date) is None)):
      current_date = current_date + timedelta(days=1)
      if (current_date >= expiration) or (current_date >= datetime.now().date()):
        return None

    if not strategy.checkEntry(underlying, current_date):
      current_date = current_date + timedelta(days=1)
      continue

    entry_vix = util.connector.query_midprice_underlying("^VIX", current_date)
    if ((strategy.min_vix_entry is not None) and (entry_vix < strategy.min_vix_entry)):
      print("VIX below minimum VIX " + str(strategy.min_vix_entry))
      current_date = current_date + timedelta(days=1)
      continue

    entry_underlying = util.connector.query_midprice_underlying(
        underlying, current_date)
    if (strategy.sma_window is not None):
      sma_results = util.connector.query_sma(
          underlying, current_date, strategy.sma_window)
      sma_sum = 0
      for sma_result in sma_results:
        sma_sum += sma_result[0]
      sma = sma_sum / len(sma_results)
      if (entry_underlying > sma):
        print("entry_underlying > sma")
        current_date = current_date + timedelta(days=1)
        continue

    combo = strategy.makeCombo(underlying, current_date, expiration, 1)

    if combo is None:
      current_date = current_date + timedelta(days=1)
      continue

    if ((strategy.min_iv_entry is not None) and not (checkMinIV(combo, strategy.min_iv_entry))):
      combo = None
      current_date = current_date + timedelta(days=1)
      continue

    if strategy.checkCombo(underlying, combo):
      break

    else:
      combo = None
      current_date = current_date + timedelta(days=1)
      continue

  if combo is None:
    print("combo is None")
    return None

  # scale up
  min_exp = combo.getMinExpiration()
  if min_exp is None:
    return None

  position_size = int(risk_capital / abs(min_exp))
  if position_size == 0:
    print("Too little capital. Minimum required: " + str(abs(min_exp)))
    return None

  # set fixed quantity
  if quantity != None:
    position_size = quantity

  positions = combo.getPositions()
  for position in positions:
    position.amount = position.amount * position_size
  min_exp = min_exp * position_size

  entry_date = current_date
  entry_price = util.getEntryPrice(combo)

  strikes = ""
  for position in combo.getPositions():
    if strikes != "":
      strikes = strikes + "/"
    if position is not None:
      strikes = strikes + str(int(position.option.strike))
    else:
      strikes = strikes + "x"

  iv_legs = ""
  for position in combo.getPositions():
    if iv_legs != "":
      iv_legs = iv_legs + "/"
    if position is not None:
      iv = util.connector.select_iv(position.option.entry_date, position.option.underlying,
                                    position.option.expiration, position.option.type, position.option.strike)
      iv_legs = iv_legs + format(float(iv), '.2f')
    else:
      iv_legs = iv_legs + "x"

  # loop to check exit for each day
  while flying:

    current_date = current_date + timedelta(days=1)

    if (current_date >= expiration) or (current_date >= datetime.now().date()):
      flying = False

    if (xnys.is_session(pd.Timestamp(current_date, tz=pytz.UTC)) == False):
      continue

    elif (util.connector.query_midprice_underlying(underlying, current_date) is None):
      continue

    # adjust
    dte = (expiration - current_date).days
    combo, realized_pnl, adjustment_counter = strategy.adjust(
        underlying, combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, adjustment_counter)

    # exit
    current_pnl = util.getCurrentPnLCombo(combo, current_date) + realized_pnl

    if current_pnl is None:
      print("current_pnl is None")
      return None

    if (round(current_pnl, 2) < round(min_exp, 2)):
      print("current_pnl: " + str(round(current_pnl, 2)))
      print("min_exp: " + str(round(min_exp, 2)))
      print("not possible: current_pnl < min_exp)")
      continue

    daily_pnls_dict[current_date] = format(
        float(current_pnl - previouspnl), '.2f')
    previouspnl = current_pnl
    dit = (current_date - entry_date).days

    exit_criterion = strategy.checkExit(
        underlying, combo, dte, current_pnl, min_exp, entry_price, current_date, expiration, dit, position_size)
    if exit_criterion == None and not flying:
      exit_criterion = "exp"
    if exit_criterion != None:

      daily_pnls = pd.DataFrame.from_dict(daily_pnls_dict, orient='index')
      daily_pnls = daily_pnls.reindex(daily_pnls.index.rename('date'))
      daily_pnls.index = pd.to_datetime(daily_pnls.index)
      daily_pnls.sort_index(inplace=True)
      daily_pnls.columns = ['pnl']

      return {'entry_date': entry_date, 'expiration': expiration, 'exit_date': current_date, 'entry_underlying': str(format(float(entry_underlying), '.2f')), 'entry_vix': entry_vix, 'strikes': strikes, 'iv_legs': iv_legs, 'entry_price': str(format(float(entry_price / position_size), '.2f')), 'dte': dte, 'dit': dit, 'pnl': str(format(float(current_pnl), '.2f')), 'dailypnls': daily_pnls, 'max_risk': str(format(float(min_exp), '.2f')), 'position_size': position_size, 'percentage': str(format(float(round((float(current_pnl) / abs(min_exp)) * 100, 2)), '.2f')) + '%', 'exit': exit_criterion}
