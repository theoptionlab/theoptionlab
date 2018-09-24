# -*- coding: utf-8 -*-
from __future__ import division
from util import util
from util import sql_connector
from datetime import timedelta, datetime 


def fly(strategy, risk_capital, entrydate, expiration): 
    
    flying = True 
    dailypnls = {}
    previouspnl = 0
    rh = 0 
    realized_pnl = 0
    current_date = entrydate 
    max_date = current_date
        
    if strategy.patient_entry: 
        current_date = entrydate - timedelta(days=strategy.patient_days_before)
        max_date = entrydate + timedelta(days=strategy.patient_days_after)

    while (current_date <= max_date): 
                
        combo = None
        
        while (sql_connector.check_holiday(strategy.underlying, current_date) == True): 
            current_date = current_date + timedelta(days=1)
            if (current_date >= expiration) or (current_date >= datetime.now().date()): 
                return None 
            
        if not strategy.checkEntry(current_date): 
            current_date = current_date + timedelta(days=1)
            continue 

        combo = strategy.makeCombo(current_date, expiration, 1)
        
        if combo is None: 
            current_date = current_date + timedelta(days=1)
            continue
        
        if strategy.checkCombo(combo): 
            break 
        
        else:
            combo = None 
            current_date = current_date + timedelta(days=1)
            continue 

    if combo is None: return None 
    

    # size up 
    max_risk = combo.getMaxRisk()
    
    position_size = int(risk_capital/abs(max_risk))
        
    positions = combo.getPositions()
    for position in positions: 
        position.amount = position.amount * position_size
        
    entry_date = current_date 
    
    entry_price = util.getEntryPrice(combo) 
    max_risk = max_risk * position_size

    
    # loop to check exit for each day 
    while flying:  
                                
        current_date = current_date + timedelta(days=1) 
        
        if current_date.isoweekday() in set((6, 7)):
            current_date += timedelta(days=8 - current_date.isoweekday())

        if (current_date >= expiration) or (current_date >= datetime.now().date()): 
            return None 
        
        if sql_connector.check_holiday(strategy.underlying, current_date): 
            continue  

        dte = (expiration - current_date).days
        
        
        # adjust 

        combo, realized_pnl, rh = strategy.adjust(combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, rh)
        

        # exit 
        
        current_pnl = util.getCurrentPnL(combo, current_date) + realized_pnl
        
        if current_pnl < (max_risk): 
            print "not possible: current_pnl < (max_risk)"
            continue
        
        if current_pnl is None: 
            return None 

        dailypnls[current_date] = current_pnl - previouspnl
        previouspnl = current_pnl 
        dit = (current_date - entry_date ).days
        exit_criterion = strategy.checkExit(combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size)
        
        if exit_criterion != None:
            
            strikes = ""
            for position in combo.getPositions(): 
                if strikes != "": strikes = strikes + "/"
                strikes = strikes + str(int(position.option.strike))
                
            return {'exit': exit_criterion, 'entry_date': entry_date, 'strikes': strikes, 'exit_date': current_date, 'exit_date': current_date, 'entry_price': entry_price/position_size, 'pnl': current_pnl, 'dte' : dte, 'dit' : dit, 'dailypnls' : dailypnls, 'max_risk' : max_risk, 'position_size' : position_size}
 
