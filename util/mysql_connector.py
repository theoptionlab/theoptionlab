import MySQLdb
from private import settings


class MyDB(object):
    _db_connection = None
    _db_cur = None

    def __init__(self):
        self._db_connection = MySQLdb.connect(host="localhost", user=settings.db_username, passwd=settings.db_password, db="optiondata") 
        self._db_cur = self._db_connection.cursor()

    def query(self, query):
        return self._db_cur.execute(query)

    def __del__(self):
        self._db_connection.close()


def check_holiday(underlying, date):
    query = "SELECT COUNT(*) FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(date) + "'"
    db = MyDB()
    db.query(query)
    row = db._db_cur.fetchone()
    if (row[0] == 0): 
        return True
    else: 
        return False 


def select_strike_by_delta(quotedate, underlying, expiration, option_type, indelta): 
    db = MyDB() 
    query = "SELECT strike, delta FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(expiration) + "' AND option_type = '" + option_type + "' ORDER BY ABS(delta - " + str(indelta) + ") LIMIT 1;"
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None:
#         print query 
        return None
    strike = row[0]
    return strike 


def select_expiration(quotedate, underlying, option_type, days): 
    db = MyDB() 
    query = "SELECT DISTINCT expiration, root, datediff(expiration, '" + str(quotedate) + "') AS difference FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(quotedate) + "' AND option_type = '" + option_type + "' AND expiration >= '" + str(quotedate) + "' AND expiration <= DATE_ADD('" + str(quotedate) + "', INTERVAL " + str(days + 50) + " DAY)" + " AND expiration >= DATE_ADD('" + str(quotedate) + "', INTERVAL " + str(days - 50) + " DAY) ORDER BY ABS(difference - " + str(days) + ") ASC LIMIT 1;"
#     print query
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None:
#         print query 
        return None
    expiration = row[0]
    return expiration

      
def select_delta(quotedate, underlying, expiration, option_type, strike):
    db = MyDB()
    query = "SELECT delta FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(expiration) + "' AND option_type = '" + option_type + "' AND strike = '" + str(strike) + "'"
    db.query(query)
    row = db._db_cur.fetchone()
    delta = row[0]
    return delta 


def select_theta(quotedate, option):   
    db = MyDB()
    query = "SELECT theta FROM optiondata WHERE underlying_symbol = '" + option.underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(option.expiration) + "' AND option_type = '" + option.type + "' AND strike = '" + str(option.strike) + "'"
    db.query(query)
    row = db._db_cur.fetchone()
    theta = row[0]
    return theta 


def select_strikes(underlying, quotedate, expiration):   
    db = MyDB()
    query = "SELECT DISTINCT strike FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(expiration) + "'"
    db.query(query)
    strikes = db._db_cur.fetchall()
    return strikes 


def select_strikes_midprice(underlying, quotedate, expiration, option_type, divisor):   
    db = MyDB()
    query = "SELECT strike, bid_1545, ask_1545 FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(expiration) + "' AND option_type = '" + option_type + "' AND strike % " + str(divisor) + " = 0 ORDER BY strike asc" 
#     print query
    db.query(query)
    results = db._db_cur.fetchall()
    return results

    
def check_option(underlying, strike, current_date, expiration): 
    db = MyDB()
    query = "SELECT EXISTS (SELECT * FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND strike = '" + str(strike) + "' AND quote_date = '" + str(current_date) + "' AND expiration = '" + str(expiration) + "')"
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None:
#         print query 
        return None 
    result = row[0] 
#     if result == 0: 
#         print query
    return result

        
def query_midprice_underlying(underlying, quotedate): 
    if quotedate == None: quotedate = query_maxdate()
    db = MyDB()
    query = "SELECT distinct underlying_bid_1545, underlying_ask_1545 FROM optiondata WHERE underlying_symbol = '" + str(underlying) + "' AND quote_date = '" + str(quotedate) + "'"
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None:
#         print query
        print "row is None"
        return None
    midprice = (row[0] + row[1]) / 2
    return float(midprice)


def query_midprice(quotedate, option, printalot=False): 
    if quotedate == None: quotedate = query_maxdate()
    db = MyDB()
    query = "SELECT bid_1545, ask_1545 FROM optiondata WHERE underlying_symbol = '" + option.underlying + "' AND quote_date = '" + str(quotedate) + "' AND expiration = '" + str(option.expiration) + "' AND strike = '" + str(option.strike) + "' AND option_type = '" + option.type + "'"    
    db.query(query)
    if printalot: print query 
    row = db._db_cur.fetchone()
    if row == None: 
#         if printalot: print query 
        return None
    midprice = (row[0] + row[1]) / 2
#     if printalot: print str(quotedate) + ": strike=" + str(option.strike) + " type=" + option.type + " bid_1545=" + str(row[0]) + " ask_1545=" + str(row[1]) + " midprice=" + str(midprice)  
    return float(midprice)


def query_maxdate():
    db = MyDB()
    db.query("SELECT MAX(quote_date) FROM optiondata")
    row = db._db_cur.fetchone()
    maxdate = row[0]
    return maxdate 


def check_exists(underlying, date):
    db = MyDB()
    query = "SELECT EXISTS(SELECT 1 FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND expiration = '" + str(date) + "')"
    db.query(query)
    row = db._db_cur.fetchone()
    return row[0]


def query_expiration_before(underlying, strike, current_date, later_expiration):
    db = MyDB() 
    query = "SELECT DISTINCT expiration FROM optiondata WHERE quote_date = '" + str(current_date) + "' AND underlying_symbol = '" + underlying + "' AND expiration > '" + str(current_date) + "' AND expiration < '" + str(later_expiration) + "' AND strike = '" + str(strike) + "' ORDER BY expiration DESC LIMIT 1"
#     print query
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None: 
        return None 
    return row[0]


def query_teenie_strike(underlying, current_date, expiration, option_type):
    db = MyDB() 
    query = "SELECT strike FROM optiondata WHERE underlying_symbol = '" + underlying + "' AND quote_date = '" + str(current_date) + "' AND expiration ='" + str(expiration) + "' AND ask_1545 = '0.05' AND option_type = '" + option_type + "' ORDER BY strike DESC LIMIT 1"
    db.query(query)
    row = db._db_cur.fetchone()
    if row == None: 
        return None 
    return row[0]

