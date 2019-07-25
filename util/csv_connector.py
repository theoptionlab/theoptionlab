import pandas as pd 
from datetime import datetime, timedelta 


def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot)) 
     

class MyCSV(object):

    def __init__(self):
        self.dataset = pd.read_csv("/Users/kathrindentler/Dropbox/Workspace/theoptionlab/optiondata/spx.csv")
        self.dataset['delta'] = pd.to_numeric(self.dataset['delta']) 
        self.dataset['quote_date'] = self.dataset['quote_date'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").date() )
        self.dataset['expiration'] = self.dataset['expiration'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d").date() )
        

    def check_holiday(self, underlying_symbol, quote_date):
        return len(self.dataset[self.dataset.quote_date == quote_date].index) == 0 
    
    def query_midprice_underlying(self, underlying_symbol, quote_date): 
        return self.dataset[self.dataset.quote_date == quote_date].underlying_mid_1545.head(1).item()

    def select_expiration(self, quote_date, underlying_symbol, option_type, days): 
        expirations_list = self.dataset[self.dataset.quote_date == quote_date].expiration.unique()
           
        searched_date = quote_date + timedelta(days=days) 
        return nearest(expirations_list,searched_date)   
    

    def select_strike_by_delta(self, quote_date, underlying_symbol, expiration, option_type, indelta, divisor=1):
        
        filtered = self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration == expiration) & (self.dataset.strike % divisor == 0)]
        return filtered.iloc[(filtered.delta - indelta).abs().argsort()].strike.head(1).item()
                     

    def select_strike_by_midprice(self, quote_date, underlying_symbol, expiration, option_type, inmidprice, divisor=1):
        filtered = self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration == expiration) & (self.dataset.strike % divisor == 0)]
        return filtered.iloc[(filtered.mid_1545 - inmidprice).abs().argsort()].strike.head(1).item()


    def query_midprice(self, quote_date, option, printalot=False): 
        filtered = self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration == option.expiration) & (self.dataset.strike == option.strike)]
        if len(filtered) == 0: return None 
        else: return filtered.mid_1545.head(1).item()


    def check_option(self, underlying_symbol, strike, quote_date, expiration):
        return len(self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration == expiration) & (self.dataset.strike == strike)]) != 0 


    def query_expiration_before(self, underlying_symbol, strike, quote_date, later_expiration):
        filtered = self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration > quote_date) & (self.dataset.expiration < later_expiration) & (self.dataset.strike == strike)].expiration
        result = filtered.sort_values(ascending=False)
        return result.head(1).item() 
        

    def select_delta(self, quote_date, underlying_symbol, expiration, option_type, strike):
        filtered = self.dataset[(self.dataset.quote_date == quote_date) & (self.dataset.expiration == expiration) & (self.dataset.strike == strike)]
        return filtered.strike.item() 
    
    