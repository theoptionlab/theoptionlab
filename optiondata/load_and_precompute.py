#!/usr/bin/python
from private import settings
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import os
import psycopg2
from util import util
from datetime import datetime
from optiondata import precompute_greeks


pd.options.mode.chained_assignment = None


def load(underlyings, dir, precompute_all):

  print("load: " + str(underlyings))
  print()

  engine = create_engine(
      "postgresql://"
      + settings.db_username
      + ":"
      + settings.db_password
      + "@127.0.0.1/optiondata"
  )
  table = "optiondata"

  db = psycopg2.connect(
      host="localhost",
      user=settings.db_username,
      password=settings.db_password,
      database="optiondata",
  )
  cur2 = db.cursor()

  counter = 0
  dates_from_dir = set()
  dates_in_db = set()
  dates_to_load = set()

  # traverse root directory, and list directories as dirs and files as files
  # get all dates that need to be processed

  for root, dirs, files in os.walk(dir):
    for file in files:
      if file.endswith(".zip"):
        index = file.index("_") + 1
        file_datestring = file[index: (index + 10)]
        dates_from_dir.add(file_datestring)

  for underlying in underlyings:

    query = (
        "SELECT DISTINCT quote_date FROM optiondata WHERE underlying_symbol = '"
        + underlying
        + "' AND quote_date IN "
        + str(dates_from_dir).replace("{", "(").replace("}", ")")
        + ""
    )

    cur2.execute(query)
    rows = cur2.fetchall()
    for row in rows:
      dates_in_db.add(str(row[0]))

    dates_to_load = dates_from_dir - dates_in_db
    print("dates_from_dir: " + str(len(dates_from_dir)))
    print("dates_in_db: " + str(len(dates_in_db)))
    print("dates_to_load: " + str(len(dates_to_load)))
    print()
    exit

    for date in sorted(dates_to_load):

      if ((underlying in util.startdates) and (datetime.strptime(date, '%Y-%m-%d').date() > util.startdates[underlying])) or (underlying not in util.startdates):

        unzippedpath = ""
        counter += 1
        file = "UnderlyingOptionsEODQuotes_" + str(date) + ".zip"
        print(str(counter) + "\t" + date + "\t" + underlying + "\t" + file)
        currentdir = dir
        if currentdir.endswith("/optiondata/"):
          currentdir = currentdir + date[0:4] + "/"

        datafilepath = currentdir + file
        unzippedpath = util.unzip(datafilepath)

        if unzippedpath is not None:

          df = pd.read_csv(
              unzippedpath,
              header=0,
              dtype={
                  "underlying_symbol": object,
                  "quote_date": object,
                  "root": object,
                  "expiration": object,
                  "strike": np.float64,
                  "option_type": object,
                  "open": np.float64,
                  "high": np.float64,
                  "low": np.float64,
                  "close": np.float64,
                  "trade_volume": np.int64,
                  "bid_size_1545": np.int64,
                  "bid_1545": np.float64,
                  "ask_size_1545": np.int64,
                  "ask_1545": np.float64,
                  "underlying_bid_1545": np.float64,
                  "underlying_ask_1545": np.float64,
                  "bid_size_eod": np.int64,
                  "bid_eod": np.float64,
                  "ask_size_eod": np.int64,
                  "ask_eod": np.float64,
                  "underlying_bid_eod": np.float64,
                  "underlying_ask_eod": np.float64,
                  "vwap": object,
                  "open_interest": np.float64,
                  "delivery_code": object,
              },
          )

          filtered = df[(df["underlying_symbol"] == underlying)]

          if underlying == "^SPX":
            filtered = filtered[
                (filtered.root != "BSZ") & (filtered.root != "BSK")
            ]  # filter out binary options

          filtered["option_type"] = filtered.option_type.str.lower()
          filtered["mid_1545"] = (
              filtered["bid_1545"] + filtered["ask_1545"]) / 2
          filtered["underlying_mid_1545"] = (
              filtered["underlying_bid_1545"] +
              filtered["underlying_ask_1545"]
          ) / 2

          if len(filtered.index) > 0:
            print(str(len(filtered.index)))
            filtered.to_sql(
                table,
                engine,
                if_exists="append",
                index=False,
                chunksize=1000,
            )
            db.commit()

        if (unzippedpath != "") and (unzippedpath is not None):
          os.remove(unzippedpath)

    if precompute_all:
      precompute_counter = 0
      for date_in_db in sorted(dates_in_db):
        counter += 1
        print(str(counter) + ": " + date_in_db)
        precompute_greeks.precompute("optiondata", date_in_db, underlying, True)

  print("Done loading data \n")

  db.close()
  return dates_to_load
