from datetime import datetime, time, timedelta
import math

from util import postgresql_connector 
import pandas 

from pandas.tseries.holiday import get_calendar, HolidayCalendarFactory, GoodFriday
from py_vollib import black_scholes
from scipy.interpolate import InterpolatedUnivariateSpline as interpol
import workdays
import zipfile 

import numpy as np 
from private import settings
import scipy.stats as st

years = ([0.0, 1 / 360, 1 / 52, 1 / 12, 2 / 12, 3 / 12, 6 / 12, 12 / 12])
functions_dict = {}

df_yields = pandas.read_csv(settings.path_to_libor_csv)
cols = ['date', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12']
df_yields.columns = cols
df_yields['date'] = pandas.to_datetime(df_yields['date'])
df_yields.set_index('date', inplace=True)

entries = []

ratio = 100
lower_ul = 1
upper_ul = 1000000
dividend = 0
commissions = 1.25
connector = postgresql_connector.MyDB()

interest = 0.0225
yeartradingdays = 252

cal = get_calendar('USFederalHolidayCalendar')  # Create calendar instance
cal.rules.pop(7)  # Remove Veteran's Day rule
cal.rules.pop(6)  # Remove Columbus Day rule
tradingCal = HolidayCalendarFactory('TradingCalendar', cal, GoodFriday)

dr = pandas.date_range(start='2010-06-01', end='2019-01-01')

cal1 = tradingCal()
holidays = cal1.holidays(start=dr.min(), end=dr.max()).date


class Strategy(object): 
    
    def __init__(self, patient_days_before = 0, patient_days_after = 0, cheap_entry = None, down_day_entry = None, patient_entry = None, min_vix_entry = None, max_vix_entry = None, dte_entry = None, els_entry = None, ew_exit = None, pct_exit = None, dte_exit = None, dit_exit = None, deltatheta_exit = None, tp_exit = None, sl_exit = None, delta = None):
        
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
        self.delta = delta

    def setParameters(self, patient_days_before, patient_days_after, cheap_entry, down_day_entry, patient_entry, min_vix_entry, max_vix_entry, dte_entry, els_entry, ew_exit, pct_exit, dte_exit, dit_exit, deltatheta_exit, tp_exit, sl_exit, delta):
        
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
        self.delta = delta

    def checkEntry(self, underlying, current_date):
        return True
    
    def checkCombo(self, underlying, combo):
        return True 
    
    def adjust(self, underying, combo, current_date, realized_pnl, entry_price, expiration, position_size, dte, rh):
        return combo, realized_pnl, rh
    
    def checkExit(self):
        return False
      
      
class Option():

    def __init__(self, entry_date, underlying, strike, expiration, sort):
        
        result = connector.check_option(underlying, strike, entry_date, expiration) 
            
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
        
        if ((lower_expiration_line == None) and (upper_expiration_line == None)): 
            return None  
        
        max_risk = min(lower_expiration_line, upper_expiration_line)
        
        return max_risk

    def append(self, position):
        self.positions.append(position)

    def close_position(self, position):
        if position in self.positions:
            self.positions.remove(position) 

    
class PutButterfly(Combo):

    def __init__(self, upperlongposition, shortposition, lowerlongposition):
        self.upperlongposition = upperlongposition
        self.shortposition = shortposition
        self.lowerlongposition = lowerlongposition
        self.positions = self.upperlongposition, self.shortposition, self.lowerlongposition 
        
#     def getPositions(self):
#         return self.positions 


class PutCreditSpread(Combo):
    
    def __init__(self, shortposition, longposition):
        self.shortposition = shortposition
        self.longposition = longposition
        self.positions = self.shortposition, self.longposition 
        
#     def getPositions(self):
#         return self.positions


class Strangle(Combo):
    
    def __init__(self, putposition, callposition):
        self.putposition = putposition
        self.callposition = callposition
        self.positions = self.putposition, self.callposition 
        
#     def getPositions(self):
#         return self.positions
    
    
class IronButterfly(Combo):
    
    def __init__(self, longcallposition, shortcallposition, shortputposition, longputposition):
        self.longcallposition = longcallposition
        self.shortcallposition = shortcallposition
        self.shortputposition = shortputposition
        self.longputposition = longputposition
        self.positions = self.longcallposition, self.shortcallposition, self.shortputposition, self.longputposition
        
#     def getPositions(self):
#         return self.positions


class Condor(Combo):
    
    def __init__(self, pcs_longposition, pcs_shortposition, pds_shortposition, pds_longposition):
        self.pcs_longposition = pcs_longposition
        self.pcs_shortposition = pcs_shortposition
        self.pds_shortposition = pds_shortposition
        self.pds_longposition = pds_longposition
        self.positions = self.pcs_longposition, self.pcs_shortposition, self.pds_shortposition, self.pds_longposition
        
#     def getPositions(self):
#         return self.positions
    
    
class BWB(PutButterfly):
    
    def __init__(self, upperlongposition, rolledlongposition, cs_shortposition, lowerlongposition):
        super(BWB, self).__init__(upperlongposition, cs_shortposition, lowerlongposition)
        self.rolledlongposition = rolledlongposition
        
    # todo 
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
        
    def close_combo(self, combo):
        if combo in self.combos:
            self.combos.remove(combo) 

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
        ref = datetime.combine(reference, time(15))
            
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
    midprice = connector.query_midprice(current_date, option)
    position = Position(option, midprice, position_size)
    return position 


def getCurrentPnLPosition(position, current_date):
    
    current_commissions = commissions * (abs(position.amount) * 2)  # buy and sell
    midprice = None 
    
    # if option is expired, compute theoretical price 
    if current_date >= position.option.expiration:
        current_date = position.option.expiration 
        midprice = bs_option_price(position.option.underlying, position.option.expiration, position.option.type, position.option.strike, current_date)
        current_commissions = commissions * (abs(position.amount))  # expired, only commissions for entry
    
    while midprice is None: 

        midprice = connector.query_midprice(current_date, position.option)
        
        if midprice is None: 
            current_date = current_date - timedelta(1)
            continue 

    current_price = (midprice * position.amount)
    entry_price = (position.entry_price * position.amount)
    currentpnl = ((current_price - entry_price) * ratio) - current_commissions
    return currentpnl


def getCurrentPnLCombo(combo, current_date):
    currentpnl = 0       
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            positionPnL = getCurrentPnLPosition(position, current_date)
            if positionPnL is None: return None 
            currentpnl += positionPnL
    return currentpnl


def getCurrentPnLGroup(group, current_date):
    current_pnl = 0
    combos = group.getCombos()
    for combo in combos: 
        if combo is None: 
            print("combo is None")
        combo_pnl = getCurrentPnLCombo(combo, current_date) 
        if combo_pnl is not None: 
            current_pnl += combo_pnl
        else: print("combo_pnl is None")
    return current_pnl


def getEntryPrice(combo):
    entry_price = 0
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            entry_price += (position.entry_price * position.amount)
    return entry_price


def getDelta(combo, current_date):

    delta_sum = 0 
    
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            delta = connector.select_delta(current_date, position.option.underlying, position.option.expiration, position.option.type, position.option.strike) 
            if delta is not None: 
                delta_sum += delta * position.amount
    
    return delta_sum


def getDeltaGroup(group, current_date):

    delta_sum = 0 

    for combo in group.getCombos(): 
        delta_sum += getDelta(combo, current_date) 
        
    return delta_sum


def getVega(combo, current_date):

    vega_sum = 0 
    
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            vega = connector.select_vega(current_date, position.option.underlying, position.option.expiration, position.option.type, position.option.strike)       
            if vega is not None: 
                vega_sum += vega * position.amount 
    
    return vega_sum 


def getVegaGroup(group, current_date):

    vega_sum = 0 

    for combo in group.getCombos(): 
        vega_sum += getVega(combo, current_date) 
        
    return vega_sum 


def getThetaGroup(group, current_date):

    theta_sum = 0 

    for combo in group.getCombos(): 
        theta_sum += getTheta(combo, current_date) 
        
    return theta_sum  


def getTheta(combo, current_date):
    
    theta_sum = 0 
    
    positions = combo.getPositions()
    for position in positions: 
        if position is not None: 
            theta = connector.select_theta(current_date, position.option)
            if theta is not None: 
                theta_sum += (theta) * position.amount
    
    return theta_sum          
                
                
def getDeltaTheta(combo, current_date):
            
    delta_sum = getDelta(combo, current_date) 
    theta_sum = getTheta(combo, current_date) 

    deltatheta = abs(delta_sum) / abs(theta_sum)
    return deltatheta


def getDeltaThetaGroup(underlying, group, current_date, expiration):

    delta_sum = 0 
    theta_sum = 0
    
    combos = group.getCombos()
    for combo in combos: 
        
        delta_sum += getDelta(combo, current_date, expiration, underlying) 
        theta_sum += getTheta(combo, current_date, expiration, underlying) 
        
    deltatheta_exit = abs(delta_sum) / abs(theta_sum)
    return deltatheta_exit


def getLowerExpiration(combo, include_riskfree=True):
    
    lower_expiration_line = 0
    positions = combo.getPositions()
    
    for position in positions:
        
        if (position is None) or (position.entry_price is None):
            return None  
            
        rf = interest
        if include_riskfree: 
            rf = get_riskfree_libor(position.option.expiration, 0)
    
        lower_value = black_scholes.black_scholes(position.option.type, lower_ul, position.option.strike, 0, rf, 0)
        lower_expiration = ((lower_value - position.entry_price) * ratio * position.amount)
        lower_expiration_line += lower_expiration
    
    return lower_expiration_line
  
    
def getUpperExpiration(combo, include_riskfree=True):
        
    upper_expiration_line = 0
    positions = combo.getPositions()
    
    for position in positions:
        
        if (position is None) or (position.entry_price is None):
            return None

        rf = interest
        if include_riskfree: 
            rf = get_riskfree_libor(position.option.expiration, 0)
            
        upper_value = black_scholes.black_scholes(position.option.type, upper_ul, position.option.strike, 0, rf, 0)
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
    
    butterflies = group.getCombos()
    
    for combo in butterflies: 
        
        lower_expiration_line += getLowerExpiration(combo)
        upper_expiration_line += getUpperExpiration(combo)
    
    percentage = int(round((upper_expiration_line / lower_expiration_line) * ratio))
    return {'lower_expiration_line': lower_expiration_line, 'upper_expiration_line': upper_expiration_line, 'percentage' : percentage}


def getQuoteforMarbleOnTop(combo, current_date, include_riskfree=True): 
    
    lowest = combo.lowerlongposition.option.strike  
    highest = combo.upperlongposition.option.strike  
        
    quote = lowest 
    max_guv = 0 
    max_quote = 0
    
    while quote < highest: 
        
        sum_guv = 0 
        positions = combo.getPositions()
        for position in positions: 
            
            expiration_time = datetime.combine(position.option.expiration, time(16))
            remaining_time_in_years = remaining_time(current_date, expiration_time)
            
            rf = interest
            if include_riskfree: 
                rf = get_riskfree_libor(current_date, remaining_time_in_years)
    
            value = black_scholes.black_scholes(position.option.type, float(quote), position.option.strike, remaining_time_in_years, rf, 0)
            guv = ((value - position.entry_price) * ratio * position.amount)
            sum_guv += guv
        
        if (sum_guv > max_guv): 
            max_guv = sum_guv
            max_quote = quote 

        quote += 1
    
    return max_quote 
        
        
def getLowerBreakpoint(combo, current_date, include_riskfree=True): 
    
    lowest = combo.lowerlongposition.option.strike  
    highest = combo.upperlongposition.option.strike  
        
    quote = lowest 
    while quote < highest: 
        
        sum_guv = 0 
        positions = combo.getPositions()
        for position in positions: 
            
            expiration_time = datetime.combine(position.option.expiration, time(16))
            remaining_time_in_years = remaining_time(current_date, expiration_time)
            
            rf = interest
            if include_riskfree: 
                rf = get_riskfree_libor(current_date, remaining_time_in_years)
    
            value = black_scholes.black_scholes(position.option.type, float(quote), position.option.strike, remaining_time_in_years, rf, 0)
            guv = ((value - position.entry_price) * ratio * position.amount)
            sum_guv += guv
        
        if (sum_guv > 0): 
            return quote
        
        quote += 1
        

def getLowerBreakpointGroup(group, current_date, include_riskfree=True): 

    lowest = group.getLowest().lowerlongposition.option.strike 
    highest = group.getHighest().upperlongposition.option.strike  
        
    quote = lowest 
    while quote < highest: 
        
        sum_guv = 0
        
        combos = group.getCombos() 
        for combo in combos: 
            positions = combo.getPositions()
            for position in positions:   
                
                expiration_time = datetime.combine(position.option.expiration, time(16))
                remaining_time_in_years = remaining_time(current_date, expiration_time)
                
                rf = interest
                if include_riskfree: 
                    rf = get_riskfree_libor(current_date, remaining_time_in_years)
                
                value = black_scholes.black_scholes(position.option.type, float(quote), position.option.strike, remaining_time_in_years, rf, 0)
                guv = ((value - position.entry_price) * ratio * position.amount)
                sum_guv += guv
        
        if (sum_guv > 0): 
            return quote
        
        quote += 1
        
        
def getDownDay(underlying, date, strategy=None):
    
    down_definition = 0
    if strategy == "short_term_parking": 
        down_definition = -0.3
        
    down_day = False 
        
    previous_date = date - timedelta(days=1)
    while (connector.check_holiday(underlying, previous_date) == True): 
        previous_date = previous_date - timedelta(days=1)
                
    underlying_midprice_current = connector.query_midprice_underlying(underlying, date)
    underlying_midprice_previous = connector.query_midprice_underlying(underlying, previous_date)
    percentage_move = ((float(underlying_midprice_current) - float(underlying_midprice_previous)) / float(underlying_midprice_previous)) * 100
        
    if percentage_move < down_definition: down_day = True
    
    return down_day


def selectStrikeByPrice(price, underlying, date, expiration, option_type, divisor):
    
    results = connector.select_strikes_midprice(underlying, date, expiration, option_type, divisor)  
    
    closest_strike = None 
    
    closest_distance = 100
    closest_midprice = 0 
    
    for row in results: 
        strike = row[0]
     
        midprice = float(row[1])
        distance = abs(price - midprice)
         
        if (midprice > price) and (distance < closest_distance): 
            closest_distance = distance
            closest_strike = strike 
            closest_midprice = midprice

    return closest_strike, closest_midprice


def myround(x, base=25):
    return int(base * round(float(x) / base))


def testPCS(short_strike, current_date, underlying, expiration, position_size, width): 

    shortposition = makePosition(current_date, underlying, short_strike, expiration, "p", -position_size)
    longstrike = (short_strike - width)
    longposition = makePosition(current_date, underlying, longstrike, expiration, "p", position_size)

    if shortposition is None or longposition is None: 
        return None 
    pcs = PutCreditSpread(shortposition, longposition)
    return pcs


def bs_option_price(underlying, expiration, option_type, strike, current_date, include_riskfree=True): 
    
    price = None 
    
    while price is None: 
    
        current_quote = connector.query_midprice_underlying(underlying, current_date)
        if current_quote is None: 
            current_date = current_date - timedelta(1) 
            continue 
    
        expiration_time = datetime.combine(expiration, time(16))
        remaining_time_in_years = remaining_time(current_date, expiration_time)
        
        rf = interest
        if include_riskfree: 
            rf = get_riskfree_libor(current_date, remaining_time_in_years)
                
        price = black_scholes.black_scholes(option_type, current_quote, strike, remaining_time_in_years, rf, 0.151)
    
    return float(price)

    
def unzip(datafilepath): 
    
    archive = zipfile.ZipFile(datafilepath)
    
    for ffile in archive.namelist():
        archive.extract(ffile, settings.tempbasepath)
        unzippedpath = settings.tempbasepath + ffile
        return unzippedpath 
    

def get_riskfree_libor(date, yte):
    
    # compute only once per date 
    if date in functions_dict:
        f = functions_dict[date]

    else: 
        try: 
            df = df_yields.query('index==@date')
            dr = df.iloc[0]
            rates = ([0.0, dr['ON'] / 100, dr['w1'] / 100, dr['m1'] / 100, dr['m2'] / 100, dr['m3'] / 100, dr['m6'] / 100, dr['m12'] / 100])
            
            df_inter = pandas.DataFrame(columns=['0', 'ON', 'w1', 'm1', 'm2', 'm3', 'm6', 'm12'])
            df_inter.loc[0] = years
            df_inter.loc[1] = rates
            df_inter = df_inter.dropna(axis='columns')
            f = interpol(df_inter.loc[0], df_inter.loc[1], k=1, bbox=[0.0, 4.0])
            functions_dict[date] = f 
            
        except: 
            return (0)
#             print (str(date))
#             functions_dict[date] = 0 
#             f = functions_dict[date]
    
        
    y = float(yte)
    rf = f(y) / 100
    rf = np.round(rf, decimals=4)
    
    return rf
