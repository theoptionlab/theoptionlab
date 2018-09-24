from __future__ import division 
import MySQLdb
from util import util
from datetime import datetime 
from private import settings

date = "2018-09-14"

counter = 0

db = MySQLdb.connect(host="localhost", user=settings.db_username, passwd=settings.db_password, db="optiondata") 
cur1 = db.cursor()
cur2 = db.cursor()
cur3 = db.cursor()

query = "SELECT DISTINCT underlying_symbol FROM fullday WHERE quote_date = '" + str(date) + "'"

cur1.execute(query) 
for row in cur1.fetchall(): 
    underlying = row[0]
    
    query = "SELECT distinct underlying_bid_1545, underlying_ask_1545 FROM fullday WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(date) + "'"
    cur2.execute(query)
    row = cur2.fetchone()
    if row == None: 
        continue 
    
    underlying_price = (row[0] + row[1]) / 2
    if (underlying_price == 0) or (underlying_price < 50): 
        continue
    
    # this query needs this command to actually run: 
    # SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));
    # TODO: fix permanently
    try: 
        query = "SELECT DISTINCT `strike`, `expiration`, (select ((bid_1545+ask_1545)/2) from `fullday` where `option_type`='c' AND `id`=outer_table.`id` AND bid_1545 != 0 AND ask_1545 != 0 AND ABS(bid_1545 - ask_1545) < 0.5) AS call_mid, (select ((bid_1545+ask_1545)/2) from `fullday` WHERE bid_1545 != 0 AND ask_1545 != 0 AND ABS(bid_1545 - ask_1545) < 0.5 AND `option_type`='p' AND `strike`=outer_table.`strike` AND `expiration`=outer_table.`expiration` AND `underlying_symbol` = outer_table.`underlying_symbol` AND `quote_date` = outer_table.`quote_date`) AS put_mid FROM `fullday` as outer_table WHERE bid_1545 != 0 AND ask_1545 != 0 AND `underlying_symbol` = '" + underlying + "' AND `quote_date` = '" + date + "' AND `expiration` > DATE_ADD(`quote_date`, INTERVAL 60 DAY) GROUP BY `expiration`, `strike`"
        cur2.execute(query)
    except:
#         print query 
        continue 
        

    for row in cur2:        
        strike = row[0]
        expiration = row[1]
        callmidprice = row[2]
        putmidprice = row[3]
        
        if (callmidprice == None) or (putmidprice == None): 
            continue 
        
        if callmidprice > putmidprice: 
                        
            credit = callmidprice - putmidprice

            difference = (strike - underlying_price)
            percentage = float(((difference + credit) / underlying_price) * 100)
            
            remaining_time = util.remaining_time(datetime.strptime(str(date), "%Y-%m-%d").date(), datetime.strptime(str(expiration), "%Y-%m-%d"))
            per_annum = round((percentage / remaining_time), 2)
            
            if per_annum > 3:  # USD 12 months LIBOR
                counter += 1
                print "counter: " + str(counter)
                print "underlying: " + str(underlying) 
                print "price: " + str(float(underlying_price))
                print "strike: " + str(strike) 
                print "expiration: " + str(expiration) 
                print "call midprice: " + str(float(callmidprice)) 
                print "put midprice: " + str(float(putmidprice))
                print "credit -c+p: " + str(credit)
                print "percentage: " + str(round(percentage, 2))
                print "remaining time in years: " + str(remaining_time)
                print "percentage / remaining time: " + str(per_annum)
                print 
            
db.close()
