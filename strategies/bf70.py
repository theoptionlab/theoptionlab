# -*- coding: utf-8 -*-

# see https://theoptionlab.com/research/bf70.html

from util import util
from util import sql_connector
from util import expected_value
import collections


parameters = collections.OrderedDict()
parameters["cheap_entry"] = [None]
parameters["down_day_entry"] = [False]
parameters["patient_entry"] = [False]
parameters["min_vix_entry"] = [None]
parameters["max_vix_entry"] = [None]
parameters["dte_entry"] = [70]
parameters["els_entry"] = [None]
parameters["ew_exit"] = [False]
parameters["pct_exit"] = [None]
parameters["dte_exit"] = [7]
parameters["dit_exit"] = [None]
parameters["deltatheta_exit"] = [None]
parameters["tp_exit"] = [None]
parameters["sl_exit"] = [None] 



class bf70(util.Strategy):
    
    def makeCombo(self, current_date, expiration, position_size):

        current_quote = sql_connector.query_midprice_underlying(self.underlying, current_date)
        upperlongstrike = int(round(current_quote, -1))

        # Obere long Puts am Geld 
        upperlongposition = util.makePosition(current_date, self.underlying, upperlongstrike, expiration, "p", position_size)
        if upperlongposition is None: return None 
        # Short Puts 30 Punkte drunter 
        shortstrike = int(upperlongstrike - 30)
        shortposition = util.makePosition(current_date, self.underlying, shortstrike, expiration, "p", -2 * position_size)
        if shortposition is None: return None 
        
        # Untere long Puts 40 Punkte unter Short Puts 
        lowerlongstrike = int(upperlongstrike - 70)
        lowerlongposition = util.makePosition(current_date, self.underlying, lowerlongstrike, expiration, "p", position_size)
        if lowerlongposition is None: return None 
        
        combo = util.BWB(upperlongposition, None, shortposition, lowerlongposition)
            
        return combo


    def checkEntry(self, current_date):

        if (self.down_day_entry): 
            down_day = util.getDownDay(self.underlying, current_date, self.name)
            if (not down_day): 
                return False 
                
        return True 
    
    
    def checkCombo(self, combo):
        
        # Preis checken
        if self.cheap_entry is not None: 
            entry_price = util.getEntryPrice(combo) 
            if (entry_price > (self.cheap_entry)): 
                return False 
            
        return True 
    
    
    def checkExit(self, combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size):

        underlying_midprice = sql_connector.query_midprice_underlying(self.underlying, current_date)
    
        # 1) TP Ziel erreicht: 1,000 > 35 DTE, 800 > 28 DTE, 600 > 21 DTE, 400
        tp = 200  
        if dte <= 35: tp = 160  
        if dte <= 28: tp = 120  
        if dte <= 21: tp = 80 
        tp = tp * position_size 
        
        if current_pnl >= tp: 
            return "tp"
    
        # 2) RUT 10 Punkte unter den Short Strikes 
        if underlying_midprice < combo.shortposition.option.strike - 10: 
            return "le"
    
        # 3) Restlaufzeit ist < 40 DTE und RUT ist 60 Punkte über den Short Strikes 
        if ((dte < 40) and (underlying_midprice > combo.shortposition.option.strike + 60)): 
            return "ue"
            
        # 4) Restlaufzeit < dte_exit
        if dte < self.dte_exit: 
            return "dte"
        
        # 5) Erwartungswert < aktueller Wert 
        if self.ew_exit == True: 
            ew = expected_value.getExpectedValue(self.underlying, combo, current_date, expiration)
            if ew <= current_pnl:
                return "ew"
            
        return None 
