# -*- coding: utf-8 -*-
from __future__ import division

import collections
from datetime import datetime
import os 
import shutil 

import numpy as np
import pandas as pd

from util import util
from util import performance

import trading_calendars as tc
xnys = tc.get_calendar("XNYS")

def list_strategies(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def compute_stats(strategy_name, risk_capital, exclude=[]):

    # start with computing stats 
    equity_curve = collections.OrderedDict()
    results_table = collections.OrderedDict()
    j  = 0 
    
    path = os.getcwd()
    strategy_path = path + '/results/' + strategy_name 
    df = pd.read_csv(strategy_path + '/single_results.csv') 
    single_results = df.to_dict(orient='index')
    
    dailypnls_path = strategy_path + '/daily_pnls/' 
    for strategy_code in list_strategies(dailypnls_path):
        print (strategy_code)
        
        if (strategy_code not in exclude): 
    
            strategy_code_path = strategy_path + '/daily_pnls/' + strategy_code + "/"
    
            exits = {} 
            total_positions = 0
            total_risk = 0
            total_pnl = 0
            winners = 0 
            allwinners = 0
            allloosers = 0
            maxwinner = 0 
            loosers = 0
            maxlooser = 0 
            total_dit = 0
    
            total_daily_pnls = None 
            total = risk_capital
            running_global_peak = 0
            running_global_peak_date = datetime(2000, 1, 1).date()
            max_dd = 0 
            running_max_dd_date = datetime(2000, 1, 1).date()
    
            # compute stats for strategy 
            for key, value in single_results.items():
                if (value['strategy_code'] == strategy_code):
    
                    total_positions += int(value['position_size'])
                    
                    total_risk += value['max_risk']
                    total_pnl += value['pnl'] 
                    if value['pnl']  >= 0: 
                        allwinners += value['pnl'] 
                        winners += 1
                        if value['pnl']  > maxwinner: 
                            maxwinner = value['pnl']  
    
                    else: 
                        allloosers += value['pnl'] 
                        loosers += 1 
                        if value['pnl'] < maxlooser: 
                            maxlooser = value['pnl'] 
    
                    total_dit += value['dit']
    
                    if value['exit'] in exits: 
                        exits[value['exit']] += 1
                    else:
                        exits[value['exit']] = 1
    
    
            for key, value in exits.items():
                if util.printalot: print(str(key) + ' exit: \t' + str(value))
    
            
            # merge total_daily_pnls per strategy 
            number_of_trades = 0 
            for filename in os.listdir(strategy_code_path):
                if filename.endswith('.csv'):
                    number_of_trades += 1  
                    
                    daily_pnls = pd.read_csv(strategy_code_path + filename, parse_dates=['date'], index_col=['date'])
    
                    if (total_daily_pnls is None): 
                        total_daily_pnls = daily_pnls
                        
                    else: 
                        total_daily_pnls = pd.concat([daily_pnls, total_daily_pnls], axis=0, join='outer', ignore_index=False).groupby(['date'], as_index=True).sum()
                        total_daily_pnls.sort_index(inplace=True)
    
    
            if (total_daily_pnls is None): 
                print('no trades')
                continue
    
    
            total_daily_pnls['cum_sum'] = total_daily_pnls.pnl.cumsum() + total
            total_daily_pnls['daily_ret'] = total_daily_pnls['cum_sum'].pct_change()
            
            annualized_sharpe_ratio = performance.annualized_sharpe_ratio(np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)
            annualized_sortino_ratio = performance.annualized_sortino_ratio(np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)
            
            
            for key, value in total_daily_pnls.iterrows():
                j += 1
                total += value['pnl']
                equity_curve[j] = {'strategy': strategy_code, 'date': key.date(), 'pnl': format(float(total), '.2f')}
                                
                if total >= running_global_peak: 
                    running_global_peak = total
                    min_since_global_peak = total
                    running_global_peak_date = key
                if total < min_since_global_peak: 
                    min_since_global_peak = total
                    if total - running_global_peak <= max_dd:
                        max_dd = total - running_global_peak
                        running_max_dd_date = key
                        max_dd_percentage = round((max_dd / running_global_peak * 100), 2)  
                        max_dd_risk_percentage = round((max_dd / risk_capital * 100), 2)  
                        max_dd_duration = abs((running_global_peak_date - running_max_dd_date).days)
            
            average_pnl = int(total_pnl / number_of_trades)
            average_risk = int(total_risk / number_of_trades)
            average_percentage = round(total_pnl / abs(total_risk) * 100, 2)
            percentage_winners = int((winners / number_of_trades) * 100)
    
            try: 
                average_winner = int(allwinners / winners)
            except ZeroDivisionError:
                average_winner = 0
                
            try: 
                average_looser = int(allloosers / (number_of_trades - winners))
            except ZeroDivisionError:
                average_looser = 0
                
            average_dit = int(total_dit / number_of_trades)
            average_position_size = format(float(total_positions / number_of_trades), '.2f')
            rod = format(float(average_percentage / (total_dit / number_of_trades)), '.2f')
                
            days = (equity_curve[j]["date"] - equity_curve[1]["date"]).days
            years = round((days / 365), 2)
            
            annualized_pnl = int(total_pnl) / years 
            annualized_RoR = round((annualized_pnl / risk_capital * 100), 2)
            
            rrr = round((annualized_RoR / -max_dd_risk_percentage), 2)
    
            
            results_table[strategy_code] = {'trades': number_of_trades, 'Sharpe': annualized_sharpe_ratio, 'Sortino': annualized_sortino_ratio, 'total pnl': int(total_pnl), 'avg pnl': average_pnl, 'avg risk': average_risk, 'avg RoR %': average_percentage, 'annualized RoR%': annualized_RoR, 'max dd $': format(float(max_dd), '.2f'), 'max dd on risk %': max_dd_risk_percentage, 'max dd on previous peak %': max_dd_percentage, 'max dd date': running_max_dd_date, 'max dd duration': max_dd_duration, 'pct winners': percentage_winners, 'avg winner': average_winner, 'max winner': int(maxwinner), 'avg looser': average_looser, 'max looser': int(maxlooser), 'avg DIT': average_dit, 'avg size': average_position_size, 'avg RoR / avg DIT': rod, 'RRR': rrr}
    

    # save computed stats 
    df_curve = pd.DataFrame.from_dict(equity_curve, orient='index')
    df_curve.to_csv(strategy_path + '/results.csv')
    
    df_table = pd.DataFrame.from_dict(results_table, orient='index')
    print (df_table)
    df_table.to_html(strategy_path + '/results_table.html')


    # Copy files for web 
    shutil.copyfile(path + '/util/web/d3.js', strategy_path + '/d3.js') 
    shutil.copyfile(path + '/util/web/index.html', strategy_path + '/index.html') 
    try:
        shutil.copyfile(path + '/util/web/' + str(strategy_name) + '.html', strategy_path + '/strategy.html') 
    except Exception as e:
        print (e)
        
