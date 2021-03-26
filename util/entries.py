import calendar
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BMonthEnd
from util import util 
import collections 

c = calendar.Calendar(firstweekday=calendar.SUNDAY)
offset = BMonthEnd()


def is_third_friday_or_saturday(d):
    return (d.weekday() == 4 and 15 <= d.day <= 21) or (d.weekday() == 5 and 16 <= d.day <= 22)


# DTE-based entries. At the moment only monthlies
# Tried root to get third friday / saturday, but that is not reliable 
def getEntries(underlying, start, end, days):
    
    entries = {}

    expirations = util.connector.select_expirations(start + timedelta(days), end + timedelta(days), underlying)
    for expiration in expirations: 
        expiration = expiration[0] 
        
        if is_third_friday_or_saturday(expiration): 
            entrydate =  expiration - timedelta(days) 
        
            # try for seven days
            tries = 0
            while (not util.connector.check_exists(underlying, expiration, entrydate) and tries < 5): 
                entrydate = entrydate + timedelta(days=1)
                tries+=1
            
            if ((entrydate >= start) and (expiration <= end)): 
                entries[entrydate] = expiration

    ordered_entries = collections.OrderedDict(sorted(entries.items(), key=lambda x:x[1], reverse=False))    
    single_entries = list(ordered_entries.items())
    return single_entries 



def getDailyEntries(underlying, start, end, days):
    
    entry_dates = util.connector.select_entries(start, end, underlying)
    entries = {}
    
    for entry_date in entry_dates: 
        expiration = util.connector.select_expiration(entry_date[0], underlying, "p", days, 30)
        entries[entry_date[0]] = expiration

    ordered_entries = collections.OrderedDict(sorted(entries.items(), key=lambda x:x[1], reverse=False))   
    single_entries = list(ordered_entries.items())
    return single_entries 



# only regular options at the moment 
def getNextEntry(underlying, refDate, days):
            
    running = True
    current_date = refDate
    
    nextEntry = {}
    
    while running:
        
        year = current_date.year
        month = current_date.month
        monthcal = c.monthdatescalendar(year, month)
        third_friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]
        
                        
        nextExpiration = third_friday
        exists = util.connector.check_exists(underlying, third_friday)

        if (exists == 0):  # "expiration not found"
            third_saturday = third_friday + timedelta(days=1)
            exists = util.connector.check_exists(underlying, third_saturday)
            if (exists == 0): 
                break;
            
            else: 
                nextExpiration = third_saturday    

        dte = (nextExpiration - refDate).days

        if dte >= days: 
            running = False  
            
        else: 
            nextEntry['expiration'] = nextExpiration

        current_date += relativedelta(months=1)

    return nextEntry 

