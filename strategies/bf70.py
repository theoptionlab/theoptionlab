# -*- coding: utf-8 -*-

# results visualised on https://theoptionlab.com

import collections

from util import expected_value
from util import util

parameters = collections.OrderedDict()
parameters["patient_days_before"] = [5]
parameters["patient_days_after"] = [5]
parameters["cheap_entry"] = [None, 1.1]
parameters["down_day_entry"] = [True, False]
parameters["patient_entry"] = [True, False]
parameters["min_vix_entry"] = [None]
parameters["max_vix_entry"] = [None]
parameters["dte_entry"] = [70]
parameters["entry"] = [None]
parameters["els_entry"] = [None]
parameters["ew_exit"] = [True, False]
parameters["pct_exit"] = [None]
parameters["dte_exit"] = [7]
parameters["dit_exit"] = [None]
parameters["deltatheta_exit"] = [None]
parameters["tp_exit"] = [None]
parameters["sl_exit"] = [None] 
parameters["delta"] = [None]


class bf70(util.Strategy):
    
    def makeCombo(self, underlying, current_date, expiration, position_size):

        current_quote = util.connector.query_midprice_underlying(underlying, current_date)
        upperlongstrike = int(round(float(current_quote), -1))

        # upper long puts at the money 
        upperlongposition = util.makePosition(current_date, underlying, upperlongstrike, expiration, "p", position_size)
        if upperlongposition is None: return None 
        
        # short puts 30 points below 
        shortstrike = int(upperlongstrike - 30)
        shortposition = util.makePosition(current_date, underlying, shortstrike, expiration, "p", -2 * position_size)
        if shortposition is None: return None 
        
        # lower long puts 40 points below short puts
        lowerlongstrike = int(upperlongstrike - 70)
        lowerlongposition = util.makePosition(current_date, underlying, lowerlongstrike, expiration, "p", position_size)
        if lowerlongposition is None: return None 
        
        combo = util.BWB(upperlongposition, None, shortposition, lowerlongposition)
        return combo

    def checkEntry(self, underlying, current_date):

        if (self.down_day_entry): 
            down_day = util.getDownDay(underlying, current_date)
            if (not down_day): 
                return False 
                
        return True 
    
    def checkCombo(self, underlying, combo):
        
        # check entry price 
        if self.cheap_entry is not None: 
            entry_price = util.getEntryPrice(combo) 
            if (entry_price > (self.cheap_entry)): 
                return False 
            
        return True 
    
    def checkExit(self, underlying, combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size):

        underlying_midprice = util.connector.query_midprice_underlying(underlying, current_date)
    
        # 1) TP: 1,000 > 35 DTE, 800 > 28 DTE, 600 > 21 DTE, 400
        tp = 200  
        if dte <= 35: tp = 160  
        if dte <= 28: tp = 120  
        if dte <= 21: tp = 80 
        tp = tp * position_size 
        
        if current_pnl >= tp: 
            return "tp"
    
        # 2) RUT 10 points below the short strikes
        if float(underlying_midprice) < combo.shortposition.option.strike - 10: 
            return "le"
    
        # 3) remaining time is < 40 DTE and RUT is 60 points above the short strike 
        if ((dte < 40) and (float(underlying_midprice) > combo.shortposition.option.strike + 60)): 
            return "ue"
            
        # 4) remaining time < dte_exit
        if dte < self.dte_exit: 
            return "dte"
        
        # 5) expected value < current value 
        if self.ew_exit == True: 
            ew = expected_value.getExpectedValue(underlying, combo, current_date, expiration)
            if ew <= current_pnl:
                return "ew"
            
        return None 
