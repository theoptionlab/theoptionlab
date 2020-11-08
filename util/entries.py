import calendar
from datetime import timedelta, datetime 

from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BMonthEnd
from util import util 
import collections 

c = calendar.Calendar(firstweekday=calendar.SUNDAY)
offset = BMonthEnd()


def getNextEntry(underlying, refDate, days, regular, eom):
            
    running = True
    current_date = refDate
    
    nextEntry = {}
    
    while running:
        
        year = current_date.year
        month = current_date.month
        monthcal = c.monthdatescalendar(year, month)
        third_friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]
        
        if regular: 
                        
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


def getEntries(underlying, start, end, days, regular, eom):

    entries = {}
    running = True
    current_date = start 
    
    while running:
            
        year = current_date.year
        month = current_date.month
        monthcal = c.monthdatescalendar(year, month)
        third_friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]
        
        if regular: 
                        
            expiration = third_friday
            exists = util.connector.check_exists(underlying, third_friday)

            if (exists == 0):  # "expiration not found"
                third_saturday = third_friday + timedelta(days=1)
                
                exists = util.connector.check_exists(underlying, third_saturday)
                if (exists == 0): 
                    current_date += relativedelta(months=1)
                    print ("pass")
                    pass;
                
                else: 
                    expiration = third_saturday 
    
            entrydate = expiration - timedelta(days) 
            if (entrydate >= start) and (expiration <= end): 
                entries[entrydate] = expiration
                          
            if entrydate >= end: 
                running = False  
                
        if eom:
                        
            last_day = offset.rollforward(third_friday).date()
            
            expiration = last_day
            entrydate = last_day - timedelta(days) 
            
            exists = util.connector.check_exists(underlying, last_day)
            if (exists == 0):  # "expiration not found"
                day_before = last_day - timedelta(days=1)
                exists = util.connector.check_exists(underlying, day_before)
                if (exists == 0): 
                    print ("pass")
                    pass;
                else: 
                    expiration = day_before
                    entrydate = day_before - timedelta(days) 
            
            if (entrydate >= start) and (last_day <= end): 
                entries[entrydate] = expiration
                
            if entrydate >= end: 
                running = False  

        current_date += relativedelta(months=1)

    ordered_entries = collections.OrderedDict(sorted(entries.items(), key=lambda x:x[1], reverse=False))    
    single_entries = list(ordered_entries.items())
    return single_entries 


def getDailyEntries(underlying, start, end, days):
    entries = {}
    running = True
    current_date = start
    
    while running:
        
        current_date = current_date + timedelta(days=1) 
        
        if current_date.isoweekday() in set((6, 7)):
            current_date += timedelta(days=8 - current_date.isoweekday())
    
        if (current_date >= end) or (current_date >= datetime.now().date()): 
            running = False 
            
        elif util.connector.check_holiday(underlying, current_date): 
            continue   
        
        expiration = util.connector.select_expiration(current_date, underlying, "p", days)
        entries[current_date] = expiration

    ordered_entries = collections.OrderedDict(sorted(entries.items(), key=lambda x:x[1], reverse=False))   
    single_entries = list(ordered_entries.items())
    return single_entries 

