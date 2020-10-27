import calendar
from datetime import timedelta, datetime 

from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import BMonthEnd
from util import util 

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
    entries = []
    running = True
    current_date = start 
    
    while running:
            
        year = current_date.year
        month = current_date.month
        monthcal = c.monthdatescalendar(year, month)
        third_friday = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month][2]
        if regular: 
                                
            entry_regular = {}
            entry_regular['expiration'] = third_friday
            exists = util.connector.check_exists(underlying, third_friday)

            if (exists == 0):  # "expiration not found"
                third_saturday = third_friday + timedelta(days=1)
                
                exists = util.connector.check_exists(underlying, third_saturday)
                if (exists == 0): 
                    current_date += relativedelta(months=1)
                    continue;
                
                else: 
                    entry_regular['expiration'] = third_saturday 
    
            entry_regular['entrydate'] = entry_regular['expiration'] - timedelta(days) 
            if (entry_regular['entrydate'] >= start) and (entry_regular['expiration'] <= end): 
                entries.append(entry_regular)
                          
            if entry_regular['entrydate'] >= end: 
                running = False  
                
        if eom:
            
            last_day = offset.rollforward(third_friday).date()
            
            entry_eom = {}
            entry_eom['expiration'] = last_day
            entry_eom['entrydate'] = last_day - timedelta(days) 
            
            exists = util.connector.check_exists(underlying, last_day)
            if (exists == 0):  # "expiration not found"
                day_before = last_day - timedelta(days=1)
                exists = util.connector.check_exists(underlying, day_before)
                if (exists == 0): 
                    continue;
                else: 
                    entry_eom['expiration'] = day_before
                    entry_eom['entrydate'] = day_before - timedelta(days) 
            
            if (entry_regular['entrydate'] >= start) and (last_day <= end): 
                entries.append(entry_eom)
                
            if entry_regular['entrydate'] >= end: 
                running = False  

        current_date += relativedelta(months=1)

    sorted_entries = sorted(entries, key=lambda k: k['entrydate']) 
    return sorted_entries 


def getDailyEntries(underlying, start, end, days):
    entries = []
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
        entry = {}
        entry['entrydate'] = current_date
        entry['expiration'] = expiration
        entries.append(entry)
                
    return entries 

