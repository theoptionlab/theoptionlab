# -*- coding: utf-8 -*-
import collections
from util import util
from util import sql_connector


parameters = collections.OrderedDict()
parameters["cheap_entry"] = [None]
parameters["down_day_entry"] = [False]
parameters["patient_entry"] = [False]
parameters["min_vix_entry"] = [None]
parameters["max_vix_entry"] = [None]
parameters["dte_entry"] = [65]
parameters["els_entry"] = [None]
parameters["ew_exit"] = [False]
parameters["pct_exit"] = [None]
parameters["dte_exit"] = [37]
parameters["dit_exit"] = [None]
parameters["deltatheta_exit"] = [None]
parameters["tp_exit"] = [50,80, None]
parameters["sl_exit"] = [200,400,None]


def testCombo(closest_strike, current_date, underlying, expiration, position_size): 

    shortposition = util.makePosition(current_date, underlying, closest_strike, expiration, "p", -position_size)
    
    longstrike = (closest_strike - 30)
    longposition = util.makePosition(current_date, underlying, longstrike, expiration, "p", position_size)

    if shortposition is None or longposition is None: return None 
        
    positions = [shortposition, longposition]
    combo = util.Combo(positions)
    return combo


class bull(util.Strategy): 
    

    def makeCombo(self, current_date, expiration, position_size):
    
        closest_strike = sql_connector.select_strike_by_delta(current_date, self.underlying, expiration, "p", -10)
        entry_price = 0 
        
        while (entry_price > -2.5): 
            
            closest_strike += 5 
    
            combo = testCombo(closest_strike, current_date, self.underlying, expiration, position_size)
            if combo is None: continue 
            else: entry_price = util.getEntryPrice(combo) 
    
        return combo 


    
    def checkExit(self, combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size):
        

        if dte < self.dte_exit: 
            return "dte"
    
        # Stop Loss: x% der eingenommenen Prämie 
        if (self.sl_exit is not None):
            sl = (entry_price * self.sl_exit)
            if current_pnl <= sl:
                return "sl"
        
        # Take Profit
        if (self.tp_exit is not None): 
            tp = (-entry_price * self.tp_exit)
            if current_pnl >= tp:
                return "tp"

        
        return None 
