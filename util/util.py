# -*- coding: utf-8 -*-
import sql_connector
import calendar
import math
import scipy.stats as st
import workdays
import pandas 
from pandas.tseries.offsets import BMonthEnd
from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory, GoodFriday
from datetime import datetime, time, timedelta
from py_vollib import black_scholes

c = calendar.Calendar(firstweekday=calendar.SUNDAY)
offset = BMonthEnd()
entries = []

ratio = 100
lower_ul = 1
upper_ul = 1000000
dividend = 0
# commissions = 0
commissions = 1.25

interest = 0.001
yeartradingdays = 252

cal = get_calendar('USFederalHolidayCalendar')  # Create calendar instance
cal.rules.pop(7)  # Remove Veteran's Day rule
cal.rules.pop(6)  # Remove Columbus Day rule
tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)

dr = pandas.date_range(start='2010-06-01', end='2019-01-01')

# new instance of class
cal1 = tradingCal()
holidays = cal1.holidays(start=dr.min(), end=dr.max()).date


class Strategy(object): 
    
    def __init__(self, name, underlying, patient_days_before, patient_days_after, cheap_entry, down_day_entry, patient_entry, min_vix_entry, max_vix_entry, dte_entry, els_entry, ew_exit, pct_exit, dte_exit, dit_exit, deltatheta_exit, tp_exit, sl_exit):
        
        self.name = name 
        self.underlying = underlying 
        self.patient_days_before = patient_days_before 
        self.patient_days_after = patient_days_after 
        self.cheap_entry = cheap_entry 
        self.down_day_entry = down_day_entry
        self.patient_entry = patient_entry
        self.min_vix_entry = min_vix_entry
        self.max_vix_entry = max_vix_entry
        self.dte_entry = dte_entry
        self.els_entry = els_entry
        self.ew_exit = ew_exit
        self.pct_exit = pct_exit
        self.dte_exit = dte_exit
        self.dit_exit = dit_exit
        self.deltatheta_exit = deltatheta_exit
        self.tp_exit = tp_exit
        self.sl_exit = sl_exit

    def setParameters(self, cheap_entry, down_day_entry, patient_entry, min_vix_entry, max_vix_entry, dte_entry, els_entry, ew_exit, pct_exit, dte_exit, dit_exit, deltatheta_exit, tp_exit, sl_exit):
        
        self.cheap_entry = cheap_entry 
        self.down_day_entry = down_day_entry
        self.patient_entry = patient_entry
        self.min_vix_entry = min_vix_entry
        self.max_vix_entry = max_vix_entry
        self.dte_entry = dte_entry
        self.els_entry = els_entry
        self.ew_exit = ew_exit
        self.pct_exit = pct_exit
        self.dte_exit = dte_exit
        self.dit_exit = dit_exit
        self.deltatheta_exit = deltatheta_exit
        self.tp_exit = tp_exit
        self.sl_exit = sl_exit
        

    def checkEntry(self, current_date):
        return True
    
    def checkCombo(self, combo):
        return True 
    
    def adjust(self, combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, rh):
        return combo, realized_pnl, rh
    
    def checkExit(self):
        return False
      
      
class Option():

    def __init__(self, entry_date, underlying, strike, expiration, sort):
        
        result = sql_connector.check_option(underlying, strike, entry_date, expiration)
        if not (result == 1): 
            raise ValueError('Option not in DB')
        
        self.underlying = underlying 
        self.strike = strike
        self.expiration = expiration
        self.entry_date = entry_date
        self.type = sort


class Position():

    def __init__(self, option, entry_price, amount):
        self.option = option
        self.entry_price = entry_price
        self.amount = amount


class Combo(object):
    
    def __init__(self, positions):
        self.positions = positions
        
    def getPositions(self):
        return self.positions 
    
    def getMaxRisk(self): 
    
        el = getExpiration(self)
        lower_expiration_line = el["lower_expiration_line"]
        upper_expiration_line = el["upper_expiration_line"]
        
        if ((lower_expiration_line == 0) and (upper_expiration_line == 0)): 
            return None 
        
        max_risk = min(lower_expiration_line, upper_expiration_line)
        
        return max_risk


class PutButterfly(Combo):
    
    def __init__(self, upperlongposition, cs_shortposition, lowerlongposition):
        self.upperlongposition = upperlongposition
        self.shortposition = cs_shortposition
        self.lowerlongposition = lowerlongposition
        
    def getPositions(self):
        positions = [] 
        positions.append(self.upperlongposition)
        positions.append(self.shortposition)
        positions.append(self.lowerlongposition)
        return positions 

    
class IronButterfly(Combo):
    
    def __init__(self, longcallposition, shortcallposition, shortputposition, longputposition):
        self.longcallposition = longcallposition
        self.shortcallposition = shortcallposition
        self.shortputposition = shortputposition
        self.longputposition = longputposition
        
    def getPositions(self):
        positions = [] 
        positions.append(self.longcallposition)
        positions.append(self.shortcallposition)
        positions.append(self.shortputposition)
        positions.append(self.longputposition)
        return positions 

        
class BWB(PutButterfly):
    
    def __init__(self, upperlongposition, rolledlongposition, cs_shortposition, lowerlongposition):
        super(BWB, self).__init__(upperlongposition, cs_shortposition, lowerlongposition)
        self.rolledlongposition = rolledlongposition

    def getPositions(self):
        positions = [] 
        positions.append(self.upperlongposition)
        if self.rolledlongposition != None: positions.append(self.rolledlongposition)
        positions.append(self.shortposition)
        positions.append(self.lowerlongposition)
        return positions 

        


class Group(object):
    
    def __init__(self, combo):
        self.combos = []
        self.combos.append(combo)
        
    def append(self, combo):
        self.combos.append(combo)
    
    def getCombos(self):
        return self.combos






# probability that the price hits a barrier before expiry
# auch in makro 
def prob_hit(s, x, t, r, sd): 

    m = (r - sd ** 2 / 2)      
    if (x < s): 
        return 1 - st.norm.cdf((math.log(s / x) + m * t) / (sd * math.sqrt(t))) + (x / s) ** (2 * m / sd ** 2) * st.norm.cdf((math.log(x / s) + m * t) / (sd * math.sqrt(t)))
    else: 
        return 1 - st.norm.cdf((math.log(x / s) - m * t) / (sd * math.sqrt(t))) + (x / s) ** (2 * m / sd ** 2) * st.norm.cdf((math.log(s / x) - m * t) / (sd * math.sqrt(t)))
        
    
def excel_date(date1):
    temp = datetime(1899, 12, 30)  # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


def remaining_time(reference, expiration):
    
    if reference == None: 
        ref = datetime.now()
    else: 
        ref = datetime.combine(reference, time(15, 00))
            
    ref_excel = excel_date(ref)
    ref_date = datetime(ref.year, ref.month, ref.day)
    ref_date_excel = excel_date(ref_date)
    ref_fraction = ref_date_excel - ref_excel
    
    expiration_excel = excel_date(expiration)
    expiration_date = datetime(expiration.year, expiration.month, expiration.day)
    expiration_date_excel = excel_date(expiration_date)
    expiration_fraction = expiration_date_excel - expiration_excel
    
    fraction = expiration_fraction - ref_fraction
    networkingdays = workdays.networkdays(ref.date(), expiration.date(), holidays)
    
    remaining_time_in_years = ((networkingdays - 1) - fraction) / yeartradingdays
    return remaining_time_in_years
    

def makePosition(current_date, underlying, strike, expiration, optiontype, position_size):
    try: option = Option(current_date, underlying, strike, expiration, optiontype)
    except ValueError: 
        return None 
    midprice = sql_connector.query_midprice(current_date, option, False)   
    position = Position(option, midprice, position_size)
    return position 



def getCurrentPnLPosition(position, current_date):
    entry_price = (position.entry_price * position.amount)
    current_commissions = commissions * (abs(position.amount) * 2)  # rein und raus 
    midprice = sql_connector.query_midprice(current_date, position.option, False)
    
    if midprice == None: 
#         print "midprice is None"
        return None 
    current_price = (midprice * position.amount)
    currentpnl = ((current_price - entry_price) * ratio) - current_commissions
    return currentpnl


def getCurrentPnL(combo, current_date):
    currentpnl = 0       
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            positionPnL = getCurrentPnLPosition(position, current_date)
            if positionPnL is None: 
#                 print position.option.strike 
#                 print position.option.expiration 
#                 print current_date 
#                 print "positionPnL is None"
                return None 
            currentpnl += positionPnL
    return currentpnl


def getCurrentPnLGroup(group, current_date):
    current_pnl = 0
    combos = group.getCombos()
    for combo in combos: 
        if combo is None: 
            print "combo is None"
        combo_pnl = getCurrentPnL(combo, current_date) 
        if combo_pnl is not None: 
            current_pnl += combo_pnl
        else: print "combo_pnl is None"
    return current_pnl


def getEntryPrice(combo):
    entry_price = 0
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            entry_price += (position.entry_price * position.amount)
    return entry_price


def getDelta(combo, current_date, expiration, underlying):

    delta_sum = 0 
    
    positions = combo.getPositions()
    for position in positions: 
        
        
        delta = sql_connector.select_delta(current_date, underlying, expiration, position.option.type, position.option.strike) * position.amount        
        delta_sum += delta 
    
    return delta_sum


def getDeltaGroup(underlying, group, current_date, expiration):

    delta_sum = 0 

    for combo in group.getButterflies(): 
        delta_sum += getDelta(combo, current_date, expiration, underlying) 
        
    return delta_sum


def getTheta(combo, current_date, expiration, underlying):
    
    theta_sum = 0 
    
    positions = combo.getPositions()
    for position in positions: 
        
        theta = sql_connector.select_theta(current_date, position.option) * position.amount
        theta_sum += (theta) 
    
    return theta_sum          
                
                
def getDeltaTheta(underlying, combo, current_date, expiration):
    
    delta_sum = getDelta(combo, current_date, expiration, underlying) 
    theta_sum = getTheta(combo, current_date, expiration, underlying) 

    deltatheta = abs(delta_sum) / abs(theta_sum)
    return deltatheta


def getDeltaThetaGroup(underlying, group, current_date, expiration):

    delta_sum = 0 
    theta_sum = 0
    
    combos = group.getButterflies()
    for combo in combos: 
        
        delta_sum += getDelta(combo, current_date, expiration, underlying) 
        theta_sum += getTheta(combo, current_date, expiration, underlying) 
        
    deltatheta_exit = abs(delta_sum) / abs(theta_sum)
    return deltatheta_exit


def getLowerExpiration(combo):
    
    lower_expiration_line = 0
    positions = combo.getPositions()
    
    for position in positions:
        lower_value = black_scholes.black_scholes(position.option.type, lower_ul, position.option.strike, 0, interest, 0)
        lower_expiration = ((lower_value - position.entry_price) * ratio * position.amount)
        lower_expiration_line += lower_expiration
    
    return lower_expiration_line
  
    
def getUpperExpiration(combo):
    
    upper_expiration_line = 0
    positions = combo.getPositions()
    
    for position in positions:
        upper_value = black_scholes.black_scholes(position.option.type, upper_ul, position.option.strike, 0, interest, 0)
        upper_expiration = ((upper_value - position.entry_price) * ratio * position.amount)
        upper_expiration_line += upper_expiration
    
    return upper_expiration_line


def getExpiration(combo):
    
#     print combo.shortposition.option.expiration 
        
    lower_expiration_line = getLowerExpiration(combo)
    upper_expiration_line = getUpperExpiration(combo)
    
#     print lower_expiration_line
#     print upper_expiration_line
    
#     percentage = int(round((upper_expiration_line / lower_expiration_line) * ratio))
    return {'lower_expiration_line': lower_expiration_line, 'upper_expiration_line': upper_expiration_line}


def getExpirationGroup(group):
        
    lower_expiration_line = 0
    upper_expiration_line = 0 
    
    butterflies = group.getButterflies()
    
    for combo in butterflies: 
        
        lower_expiration_line += getLowerExpiration(combo)
        upper_expiration_line += getUpperExpiration(combo)
    
    percentage = int(round((upper_expiration_line / lower_expiration_line) * ratio))
    return {'lower_expiration_line': lower_expiration_line, 'upper_expiration_line': upper_expiration_line, 'percentage' : percentage}


def getDownDay(underlying, date, strategy):
    
    down_definition = 0
    if strategy == "short_term_parking": 
        down_definition = -0.3
        
    down_day = False 
        
    previous_date = date - timedelta(days=1)
    while (sql_connector.check_holiday(underlying, previous_date) == True): 
        previous_date = previous_date - timedelta(days=1)
                
    underlying_midprice_current = sql_connector.query_midprice_underlying(underlying, date)
    underlying_midprice_previous = sql_connector.query_midprice_underlying(underlying, previous_date)
    percentage_move = ((underlying_midprice_current - underlying_midprice_previous) / underlying_midprice_previous) * 100
        
    if percentage_move < down_definition: down_day = True
    
    return down_day

def selectStrikeByPrice(price, underlying, date, expiration, option_type, divisor):
    
    results = sql_connector.select_strikes_midprice(underlying, date, expiration, option_type, divisor)  
    
    closest_strike = None 
    
    closest_distance = 100
    closest_midprice = 0 
    
    for row in results: 
        strike = row[0]
     
        midprice  = float((row[1] + row[2]) / 2)
        distance = abs(price - midprice)
        
         
        if (midprice > price) and (distance < closest_distance): 
            closest_distance = distance
            closest_strike = strike 
            closest_midprice = midprice
            

    return closest_strike, closest_midprice


def myround(x, base=25):
    return int(base * round(float(x)/base))
