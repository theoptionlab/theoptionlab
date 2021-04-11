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
parameters["min_iv_entry"] = [None]
parameters["max_iv_entry"] = [None]
parameters["sma_window"] = [None]
parameters["dte_entry"] = [70]
parameters["els_entry"] = [None]
parameters["ew_exit"] = [False]
parameters["pct_exit"] = [0.375, 0.5, 1] 
parameters["dte_exit"] = [14]
parameters["dit_exit"] = [None]
parameters["deltatheta_exit"] = [None]
parameters["tp_exit"] = [0.1, 0.5] 
parameters["sl_exit"] = [None]
parameters["delta"] = [None]


class netzero(util.Strategy):

    def makeCombo(self, underlying, current_date, expiration, position_size):
        
        # 1x long put delta 20
        lowerlongstrike = util.connector.select_strike_by_delta(current_date, underlying, expiration, "p", -20)
        if (lowerlongstrike is None): 
            print("lowerlongstrike is None")
            return None 
        lowerlongposition = util.makePosition(current_date, underlying, lowerlongstrike, expiration, "p", position_size)
    
        # 2x short put delta 40
        shortstrike = util.connector.select_strike_by_delta(current_date, underlying, expiration, "p", -40) 
        if (shortstrike is None): 
            print("shortstrike is None")
            return None 
        shortposition = util.makePosition(current_date,  underlying, shortstrike, expiration, "p", -2 * position_size)
        
        # 1x long put delta 60
        upperlongstrike = util.connector.select_strike_by_delta(current_date, underlying, expiration, "p", -60)  
        if (upperlongstrike is None): 
            print("upperlongstrike is None")
            return None 
        upperlongposition = util.makePosition(current_date, underlying, upperlongstrike, expiration, "p", position_size)
            
        combo = util.PutButterfly(upperlongposition, shortposition, lowerlongposition) 
        return combo 

    def checkExit(self, underlying, combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size):
        
        # percentage change of short strike 
        if (self.pct_exit is not None): 

            shortdifference = self.pct_exit * -40
            short_lowerexit = -40 - shortdifference
            short_upperexit = -40 + shortdifference  

            current_shortdelta = util.connector.select_delta(current_date, underlying, expiration, combo.shortposition.option.type, combo.shortposition.option.strike)
           
            if (current_shortdelta is not None):
                if (current_shortdelta > short_lowerexit) or (current_shortdelta < short_upperexit): 
                    return "sdc"


        # T/D Ratio
        if self.deltatheta_exit is not None: 
            current_deltatheta = util.getDeltaTheta(combo, current_date)
            if (current_deltatheta is not None) and (current_deltatheta > self.deltatheta_exit):
                return "d/t"

        # time exit 
        if ((self.dte_exit is not None) and (dte < self.dte_exit)): 
            return "dte"

        # DIT (days in trade) 
        if ((self.dit_exit is not None) and (dit > self.dit_exit)): 
            return "dit"

        # Take Profit
        if ((self.tp_exit is not None) and (current_pnl >= (-max_risk * self.tp_exit))): 
            return "tp"

        return None 
