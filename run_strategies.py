# -*- coding: utf-8 -*-
from __future__ import division
from util import util
from datetime import timedelta, datetime 
import pandas  

def fly(strategy, risk_capital, entrydate, expiration): 
                
    flying = True 
    dailypnls = pandas.DataFrame(columns=['date', 'pnl'])
    
#     dailypnls = {}
    previouspnl = 0
    adjustment_counter = 0 
    realized_pnl = 0
    current_date = entrydate 
    max_date = current_date
        
    if strategy.patient_entry: 
        current_date = entrydate - timedelta(days=strategy.patient_days_before)
        max_date = entrydate + timedelta(days=strategy.patient_days_after)

    
    while (current_date <= max_date): 
                        
        combo = None
        
        while (strategy.connector.check_holiday(strategy.underlying, current_date) == True): 
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

    if combo is None: 
        print("combo is None")
        return None 

    # size up 
    max_risk = combo.getMaxRisk()
    if max_risk is None:
        return None 
    
    position_size = int(risk_capital/abs(max_risk))
        
    positions = combo.getPositions()
    for position in positions: 
        position.amount = position.amount * position_size
    max_risk = max_risk * position_size
    
    entry_date = current_date 
    entry_price = util.getEntryPrice(combo) 
    

    strikes = ""
    for position in combo.getPositions(): 
        if strikes != "": strikes = strikes + "/"
        if position is not None: 
            strikes = strikes + str(int(position.option.strike))
        else: strikes = strikes + "x"
        
    # loop to check exit for each day 
    while flying:  
                                        
        current_date = current_date + timedelta(days=1) 
        
        if current_date.isoweekday() in set((6, 7)):
            current_date += timedelta(days=8 - current_date.isoweekday())

        if (current_date >= expiration) or (current_date >= datetime.now().date()): 
            flying = False 
            
        elif strategy.connector.check_holiday(strategy.underlying, current_date): 
            continue   
        
        
        # adjust 
        dte = (expiration - current_date).days
        combo, realized_pnl, adjustment_counter = strategy.adjust(combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, adjustment_counter)
        

        # exit 
        
        current_pnl = util.getCurrentPnL(strategy.connector, combo, current_date) + realized_pnl
        
        if current_pnl is None: 
            print("current_pnl is None")
            return None 

#         if current_pnl < (max_risk): 
#             print "not possible: current_pnl < (max_risk)"
#             print current_pnl
#             continue 

        dailypnls = dailypnls.append({'date' : current_date , 'pnl' : (current_pnl - previouspnl)} , ignore_index=True)
                
        previouspnl = current_pnl 
        dit = (current_date - entry_date ).days

        if not flying: 
            return {'exit': "stop", 'entry_date': entry_date, 'strikes': strikes, 'exit_date': current_date, 'exit_date': current_date, 'entry_price': entry_price/position_size, 'pnl': current_pnl, 'dte' : dte, 'dit' : dit, 'dailypnls' : dailypnls, 'max_risk' : max_risk, 'position_size' : position_size}

        exit_criterion = strategy.checkExit(combo, dte, current_pnl, max_risk, entry_price, current_date, expiration, dit, position_size)
        if exit_criterion != None:
            dailypnls.set_index('date',inplace=True)
            return {'exit': exit_criterion, 'entry_date': entry_date, 'strikes': strikes, 'exit_date': current_date, 'exit_date': current_date, 'entry_price': entry_price/position_size, 'pnl': current_pnl, 'dte' : dte, 'dit' : dit, 'dailypnls' : dailypnls, 'max_risk' : max_risk, 'position_size' : position_size}
