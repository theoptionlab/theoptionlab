from util import util 
import math
from datetime import datetime, time
import py_lets_be_rational.exceptions as pyex
from py_vollib import black_scholes
from py_vollib.black_scholes import implied_volatility


e_spanne = 3
ratio = 100


def getExpectedValue(connector, underlying, combo, current_date, expiration): 

    current_quote = connector.query_midprice_underlying(underlying, current_date)
    
    expiration_time = datetime.combine(expiration, time(16))
    remaining_time_in_years = util.remaining_time(current_date, expiration_time)
    
    ul_for_ew = []
    sum_legs = []
    prob_touch = []
    
    if (current_quote % 10) < 5:
        atm_strike = int(current_quote / 10) * 10
    else:
        atm_strike = int((current_quote + 10) / 10) * 10
    
    try:
        atm_option = util.Option(connector, current_date, underlying, atm_strike, expiration, "p")
    except ValueError: 
        return None
    midprice = connector.query_midprice(current_date, atm_option)
    
        

    try: atm_iv = implied_volatility.implied_volatility(midprice, current_quote, atm_strike, remaining_time_in_years, util.interest, atm_option.type)

    except pyex.BelowIntrinsicException: atm_iv = 0.01
    if (atm_iv == 0): atm_iv = 0.01
    
#     print atm_iv

    
    one_sd = (atm_iv / math.sqrt(util.yeartradingdays/(remaining_time_in_years * util.yeartradingdays))) * current_quote

    lower_ul = current_quote-e_spanne*one_sd
    upper_ul = current_quote+e_spanne*one_sd
    step = (upper_ul - lower_ul) / 24 # war 1000
    

    for i in range(25): # war 1001
        
        ul_for_ew.insert(i, lower_ul + (i*step))
        
        sum_legs_i = 0 
        positions = combo.getPositions()
        for position in positions: 

#             param sigma: annualized standard deviation, or volatility
#             https://www.etfreplay.com/etf/iwm.aspx

            value = black_scholes.black_scholes(position.option.type, ul_for_ew[i], position.option.strike, remaining_time_in_years, util.interest, 0)
            guv = (value - position.entry_price) * ratio * position.amount 
            sum_legs_i += guv
            
            
            
        sum_legs.insert(i, sum_legs_i)
        
        prob = util.prob_hit(current_quote, ul_for_ew[i], remaining_time_in_years, 0, atm_iv)
        prob_touch.insert(i, prob)    
    
    sumproduct = sum([a*b for a,b in zip(sum_legs,prob_touch)])
    expected_value = round((sumproduct / sum(prob_touch)),2)
    return expected_value


def getExpectedValueGroup(underlying, group, current_date, expiration): 
    expected_value = 0
    combos = group.getCombos()
    for combo in combos: 
        expected_value += getExpectedValue(underlying, combo, current_date, expiration)
    return expected_value


# idea: Cauchy distribution or real history 

