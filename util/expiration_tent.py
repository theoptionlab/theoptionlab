import util  
from datetime import datetime, time
from py_vollib import black_scholes


def getLowerBreakpoint(combo, current_date, expiration): 
    
    expiration_time = datetime.combine(expiration, time(16, 00))
    remaining_time_in_years = util.remaining_time(current_date, expiration_time)

    lowest = combo.lowerlongposition.option.strike  
    highest = combo.upperlongposition.option.strike  
        
    quote = lowest 
    while quote < highest: 
        
        sum_guv = 0 
        positions = combo.getPositions()
        for position in positions: 
            value = black_scholes.black_scholes(position.option.type, quote, position.option.strike, remaining_time_in_years, util.interest, 0)
            guv = ((value - position.entry_price) * util.ratio * position.amount)
            sum_guv += guv
        
        if (sum_guv > 0): 
            return quote
        
        quote += 0.1
        

def getLowerBreakpointGroup(group, current_date, expiration): 
    
    expiration_time = datetime.combine(expiration, time(16, 00))
    remaining_time_in_years = util.remaining_time(current_date, expiration_time)

    lowest = group.getLowest().lowerlongposition.option.strike 
    highest = group.getHighest().upperlongposition.option.strike  
        
    quote = lowest 
    while quote < highest: 
        
        sum_guv = 0
        
        combos = group.getButterflies() 
        for combo in combos: 
            positions = combo.getPositions()
            for position in positions:   
                value = black_scholes.black_scholes(position.option.type, quote, position.option.strike, remaining_time_in_years, util.interest, 0)
                guv = ((value - position.entry_price) * util.ratio * position.amount)
                sum_guv += guv
        
        if (sum_guv > 0): 
            return quote
        
        quote += 0.1
        
        