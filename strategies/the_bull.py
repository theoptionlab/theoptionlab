# -*- coding: utf-8 -*-

# results visualised on https://theoptionlab.com

import collections
from util import util

parameters = collections.OrderedDict()
parameters["patient_days_before"] = [None]
parameters["patient_days_after"] = [None]
parameters["cheap_entry"] = [None]
parameters["down_day_entry"] = [False]
parameters["patient_entry"] = [False]
parameters["min_vix_entry"] = [None]
parameters["max_vix_entry"] = [None]
parameters["dte_entry"] = [65]
parameters["entry"] = [None]
parameters["els_entry"] = [None]
parameters["ew_exit"] = [False]
parameters["pct_exit"] = [None]
parameters["dte_exit"] = [37]
parameters["dit_exit"] = [None]
parameters["deltatheta_exit"] = [None]
parameters["tp_exit"] = [50, 80, None]
parameters["sl_exit"] = [200, 400, None]
parameters["delta"] = [None]


class bull(util.Strategy): 

    def makeCombo(self, underlying, current_date, expiration, position_size):
    
        closest_strike = util.connector.select_strike_by_delta(current_date, underlying, expiration, "p", -10, 25)
        entry_price = 0 
        
        while (entry_price > -2.5): 
            closest_strike += 25
            pcs = util.testPCS(closest_strike, current_date, underlying, expiration, position_size, 30)
            if pcs is None: continue 
            else: entry_price = util.getEntryPrice(pcs) 
    
        return pcs 
    
    def checkExit(self, underlying, combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size):
    

        if dte < self.dte_exit: 
            return "dte"
        
        # Stop Loss: x% of the credit received 
        if (self.sl_exit is not None):
            sl = (entry_price * self.sl_exit)
            if current_pnl <= sl:
                return "sl"
        
        # Take Profit
        # ratio sits in the tp_exit => could be nicer ss
        if (self.tp_exit is not None): 
            tp = (-entry_price * self.tp_exit)
            if current_pnl >= tp:
                return "tp"
        
        return None 
