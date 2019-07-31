# -*- coding: utf-8 -*-
from util import postgresql_connector 
import backtest_strategies
import time

from strategies import bf70
from strategies import netzero
from strategies import the_bull

 
from datetime import datetime 


start_time = time.time()
printalot = True

# start = datetime(2010, 6, 1).date() # vxx options since: 2010-05-28  
start = datetime(2006, 11, 1).date()

# start = datetime(2018, 1, 1).date()
end = datetime(2019, 7, 30).date()

# end = datetime.now().date()

connector = postgresql_connector.MyDB()

 
strategy = bf70.bf70(connector, "bf70", "^RUT", 5, 5, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
backtest_strategies.backtest(strategy, "bf70", 100000, printalot, start, end, bf70.parameters)
  
strategy = netzero.netzero(connector, "netzero", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
backtest_strategies.backtest(strategy, "netzero", 100000, printalot, start, end, netzero.parameters)
   
strategy = the_bull.bull(connector, "the_bull", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
backtest_strategies.backtest(strategy, "the_bull", 100000, printalot, start, end, the_bull.parameters)


print 
print("--- %s seconds ---" % (time.time() - start_time))
