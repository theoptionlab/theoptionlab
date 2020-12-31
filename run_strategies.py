# -*- coding: utf-8 -*-
from __future__ import division
from datetime import timedelta, datetime 
import pandas as pd
import trading_calendars as tc

from util import util

xnys = tc.get_calendar("XNYS")


def fly(strategy, underlying, risk_capital, entrydate, expiration): 

    flying = True 
    dailypnls = {}
    previouspnl = 0
    adjustment_counter = 0 
    realized_pnl = 0
    current_date = entrydate 
    max_date = current_date
    combo = None
        
    if strategy.patient_entry: 
        current_date = entrydate - timedelta(days=strategy.patient_days_before)
        max_date = entrydate + timedelta(days=strategy.patient_days_after)
    

    while (current_date <= max_date):
                        
        combo = None
        
        while ((xnys.is_session(pd.Timestamp(current_date)) == False) or (util.connector.query_midprice_underlying(underlying, current_date) is None)): 
            current_date = current_date + timedelta(days=1)
            if (current_date >= expiration) or (current_date >= datetime.now().date()): 
                return None 
            
        if not strategy.checkEntry(underlying, current_date): 
            current_date = current_date + timedelta(days=1)
            continue 

        combo = strategy.makeCombo(underlying, current_date, expiration, 1)
        
        if combo is None: 
            current_date = current_date + timedelta(days=1)
            continue
        
        if strategy.checkCombo(underlying, combo): 
            break 
        
        else:
            combo = None 
            current_date = current_date + timedelta(days=1)
            continue 

    if combo is None: 
        print("combo is None")
        return None 

    entry_price = util.getCurrentPnLCombo(combo, current_date) # was util.getEntryPrice(combo) but that does not include commissions
    

    # size up 
    min_exp = combo.getMinExpiration()
    if min_exp is None:
        return None 
    
    position_size = int(risk_capital / abs(min_exp))
        
    positions = combo.getPositions()
    for position in positions: 
        position.amount = position.amount * position_size
    min_exp = min_exp * position_size
    
    entry_date = current_date 
    entry_price = util.getCurrentPnLCombo(combo, current_date) # was util.getEntryPrice(combo) but that does not include commissions

    strikes = ""
    for position in combo.getPositions(): 
        if strikes != "": strikes = strikes + "/"
        if position is not None: 
            strikes = strikes + str(int(position.option.strike))
        else: strikes = strikes + "x"
        
    iv_legs = ""
    for position in combo.getPositions(): 
        if iv_legs != "": iv_legs = iv_legs + "/"
        if position is not None: 
            iv = util.connector.select_iv(position.option.entry_date, position.option.underlying, position.option.expiration, position.option.type, position.option.strike)
            iv_legs = iv_legs + format(float(iv), '.2f')
        else: iv_legs = iv_legs + "x"
    
    entry_vix = util.connector.query_midprice_underlying("^VIX", entry_date) 
    entry_underlying = util.connector.query_midprice_underlying(underlying, entry_date) 
    
    
    # loop to check exit for each day 
    while flying:  
                                        
        current_date = current_date + timedelta(days=1) 

        if (current_date >= expiration) or (current_date >= datetime.now().date()): 
            flying = False 

        if (xnys.is_session(pd.Timestamp(current_date)) == False): 
            continue   

        elif (util.connector.query_midprice_underlying(underlying, current_date) is None): 
            continue   

        # adjust 
        dte = (expiration - current_date).days
        combo, realized_pnl, adjustment_counter = strategy.adjust(underlying, combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, adjustment_counter)

        # exit 
        current_pnl = util.getCurrentPnLCombo(combo, current_date) + realized_pnl
        
        if current_pnl is None: 
            print("current_pnl is None")
            return None 

        if (current_pnl < min_exp): 
            print ("current_pnl: " + str(current_pnl))
            print ("min_exp: " + str(min_exp))
            print ("not possible: current_pnl < min_exp)")
            continue 


        dailypnls[current_date] = current_pnl - previouspnl
        previouspnl = current_pnl 
        dit = (current_date - entry_date).days

        exit_criterion = strategy.checkExit(underlying, combo, dte, current_pnl, min_exp, entry_price, current_date, expiration, dit, position_size)
        if exit_criterion == None and not flying: exit_criterion = "stop"
        if exit_criterion != None:
            return {'exit': exit_criterion, 'entry_date': entry_date, 'entry_underlying': entry_underlying, 'entry_vix': entry_vix, 'strikes': strikes, 'iv_legs': iv_legs, 'exit_date': current_date, 'exit_date': current_date, 'entry_price': format(float(entry_price / position_size), '.2f'), 'pnl': current_pnl, 'dte' : dte, 'dit' : dit, 'dailypnls' : dailypnls, 'max_risk' : min_exp, 'position_size' : position_size}
