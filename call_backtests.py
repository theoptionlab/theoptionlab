# -*- coding: utf-8 -*-
from datetime import datetime 
import time

import backtest_strategies
from private_strategies import bbf
from private_strategies import bf70_plus
from private_strategies import katzero
from util import postgresql_connector 

# from strategies import netzero  
# from strategies import the_bull 
# from strategies import bf70 
start_time = time.time()
printalot = True

start = datetime(2006, 11, 1).date()
# start = datetime(2010, 6, 1).date() # vxx options since: 2010-05-28  
# start = datetime(2017, 1, 1).date()

end = datetime(2019, 7, 31).date()
# end = datetime.now().date()

connector = postgresql_connector.MyDB()

# strategy = netzero.netzero(connector, "netzero", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
# backtest_strategies.backtest(strategy, "netzero", 100000, printalot, start, end, netzero.parameters)
#      
# strategy = the_bull.bull(connector, "the_bull", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
# backtest_strategies.backtest(strategy, "the_bull", 100000, printalot, start, end, the_bull.parameters)
#        
# strategy = bf70.bf70(connector, "bf70", "^RUT", 5, 5, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
# backtest_strategies.backtest(strategy, "bf70", 100000, printalot, start, end, bf70.parameters)

# strategy = bf70_plus.bf70plus(connector, "bf70_plus", "^RUT", 5, 5, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
# backtest_strategies.backtest(strategy, "bf70_plus", 100000, printalot, start, end, bf70_plus.parameters)

strategy = katzero.katzero(connector, "katzero", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
backtest_strategies.backtest(strategy, "katzero", 100000, printalot, start, end, katzero.parameters)

# strategy = bbf.bbf(connector, "bbf", "^RUT", 0, 0, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
# backtest_strategies.backtest(strategy, "bbf", 100000, printalot, start, end, bbf.parameters)
#   
  
print 
print("--- %s seconds ---" % (time.time() - start_time))
