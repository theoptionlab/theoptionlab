from datetime import timedelta

import pandas as pd
from util import util
import collections


def is_third_friday_or_saturday(d):
  return (d.weekday() == 4 and 15 <= d.day <= 21) or (d.weekday() == 5 and 16 <= d.day <= 22)


# DTE-based entries. At the moment only monthlies
def getEntries(underlying, start, end, days):
  entries = {}

  expirations = util.connector.select_expirations(
      start + timedelta(days), end + timedelta(days), underlying)

  for expiration in expirations:
    expiration = expiration[0]

    if is_third_friday_or_saturday(expiration):
      entrydate = expiration - timedelta(days)

      # try for some days
      tries = 0
      while (not util.connector.check_expiration(underlying, expiration, entrydate) and tries < 5):
        entrydate = entrydate + timedelta(days=1)
        tries += 1

      if ((entrydate >= start) and (expiration <= end)):
        entries[entrydate] = expiration

  ordered_entries = collections.OrderedDict(
      sorted(entries.items(), key=lambda x: x[1], reverse=False))
  single_entries = list(ordered_entries.items())
  return single_entries


def getDailyEntries(underlying, start, end, days):

  entry_dates = util.connector.select_entries(start, end, underlying)
  entries = {}

  for entry_date in entry_dates:
    expiration = util.connector.select_expiration(
        entry_date[0], underlying, "p", days, 30)
    entries[entry_date[0]] = expiration

  ordered_entries = collections.OrderedDict(
      sorted(entries.items(), key=lambda x: x[1], reverse=False))
  single_entries = list(ordered_entries.items())
  return single_entries


def getSMSEntries(underlying, start, end, days):

  entries = {}

  raw_entry_dates = pd.date_range(start, end, freq='SMS')  # SemiMonthBegin

  for entry_date in raw_entry_dates:

    if (entry_date.weekday() != 0):
      entry_date = entry_date + \
          timedelta(days=(7 - entry_date.weekday()))  # Next Monday
    entry_date = entry_date.date()

    # try for some days
    tries = 0
    while (not util.connector.check_entry(underlying, entry_date) and tries < 3):
      entry_date = entry_date + timedelta(days=1)
      tries += 1

    expiration = util.connector.select_expiration(
        entry_date, underlying, "p", days, 40)
    if expiration is not None:
      entries[entry_date] = expiration

  ordered_entries = collections.OrderedDict(
      sorted(entries.items(), key=lambda x: x[1], reverse=False))
  single_entries = list(ordered_entries.items())
  return single_entries
