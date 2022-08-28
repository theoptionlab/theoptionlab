from __future__ import division
import psycopg2
from datetime import datetime

from util import util
from private import settings


date = "2022-08-16"
print(date)
print()


counter = 0

db = psycopg2.connect(host="localhost", user=settings.db_username,
                      password=settings.db_password, database="optiondata")
cur1 = db.cursor()
query = "SELECT DISTINCT fullday_call.underlying_symbol, fullday_call.underlying_mid_1545, fullday_call.strike, fullday_call.expiration, (fullday_call.mid_1545 - fullday_put.mid_1545) AS credit FROM fullday as fullday_call JOIN fullday as fullday_put ON fullday_call.underlying_symbol = fullday_put.underlying_symbol AND fullday_call.strike = fullday_put.strike AND fullday_call.expiration = fullday_put.expiration WHERE fullday_call.underlying_mid_1545 > 100 AND fullday_call.expiration > (fullday_call.quote_date + INTERVAL '60 day') AND fullday_call.option_type = 'c' AND fullday_put.option_type = 'p' AND ABS(fullday_call.bid_1545 - fullday_call.ask_1545) < 0.5 AND fullday_call.bid_1545 != 0 AND fullday_call.ask_1545 != 0 AND ABS(fullday_put.bid_1545 - fullday_put.ask_1545) < 0.5 AND fullday_put.bid_1545 != 0 AND fullday_put.ask_1545 != 0 AND (fullday_call.mid_1545 > fullday_put.mid_1545) ORDER BY fullday_call.underlying_symbol, fullday_call.strike, fullday_call.expiration ASC;"
cur1.execute(query)
for row in cur1.fetchall():
  underlying = row[0]
  underlying_price = row[1]
  strike = row[2]
  expiration = row[3]
  credit = row[4]

  difference = (strike - underlying_price)
  percentage = float(((difference + credit) / underlying_price) * 100)

  remaining_time = util.remaining_time(datetime.strptime(
      str(date), "%Y-%m-%d").date(), datetime.strptime(str(expiration), "%Y-%m-%d"))
  per_annum = round((percentage / remaining_time), 2)

  if per_annum > 3.4:
    counter += 1
    print("counter: " + str(counter))
    print("underlying: " + str(underlying))
    print("price: " + str(float(underlying_price)))
    print("strike: " + str(strike))
    print("expiration: " + str(expiration))
    print("credit -c+p: " + str(credit))
    print("percentage: " + str(round(percentage, 2)))
    print("remaining time in years: " + str(remaining_time))
    print("percentage / remaining time: " + str(per_annum))
    print()

db.close()
