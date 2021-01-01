# -*- coding: utf-8 -*-
from __future__ import division

import collections
from datetime import datetime
from datetime import timedelta 
import itertools
import os 
import shutil 
import time

import numpy as np
import pandas as pd

import run_strategies
from util import entries
from util import performance


def dict_product(d):
    keys = d.keys()
    for element in itertools.product(*d.values()):
        yield dict(zip(keys, element))


def make_dir(path): 
    try:
        os.mkdir(path)
    except OSError:
        print ('Creation of the directory %s failed' % path)
    else:
        print ('Successfully created the directory %s ' % path)


def backtest(strategy, underlying, strategy_name, risk_capital, printalot, start, end, parameters, daily=False): 

    # create directories  
    path = os.getcwd()
    make_dir(path + '/results')
    strategy_path = path + '/results/' + strategy_name 
    if daily: strategy_path += '_daily'
    make_dir(strategy_path)
    make_dir(strategy_path + '/daily_pnls')

    if printalot: print ('strategy_name: ' + str(strategy_name))
    if printalot: print ('risk_capital: ' + str(risk_capital))
    if printalot: print ('underlying: ' + str(underlying))
    if printalot: print ('start: ' + str(start))
    if printalot: print ('end: ' + str(end))
    if printalot: print ()

    permutations = dict_product(parameters)
    if printalot: print('number of combinations: ' + str(len(list(permutations))))

    trade_log = {}
    equity_curve = collections.OrderedDict()
    results_table = collections.OrderedDict()
    
    i = 0 
    j = 0 
    
    permutations = dict_product(parameters)
    for permutation in  permutations: 
        for k, v in permutation.items(): 
            if printalot: print(k, v)
        
        strategy_code = '' 

        if permutation['cheap_entry'] is not None: strategy_code += 'C'
        if ((len(parameters['down_day_entry']) > 1) and permutation['down_day_entry']): strategy_code += 'D'
        if ((len(parameters['patient_entry']) > 1) and permutation['patient_entry']): strategy_code += 'P'
        if ((len(parameters['ew_exit']) > 1) and permutation['ew_exit']): strategy_code += 'E'
        if permutation['min_vix_entry'] is not None: strategy_code += '_MIV_' + str(permutation['min_vix_entry'])
        if permutation['max_vix_entry'] is not None: strategy_code += '_MAV_' + str(permutation['max_vix_entry'])
        if (len(parameters['dte_entry']) > 1): strategy_code += '_E' + str(permutation['dte_entry'])
        if permutation['els_entry'] is not None: strategy_code += '_EE_' + str(permutation['els_entry'])
        if permutation['pct_exit'] is not None: strategy_code += '_C' + str(int(permutation['pct_exit'] * 100))
        if ((len(parameters['dte_exit']) > 1) and permutation['dte_exit'] != 0): strategy_code += '_X' + str(permutation['dte_exit'])
        if ((len(parameters['dit_exit']) > 1) and permutation['dit_exit'] != 0): strategy_code += '_EXDIT_' + str(permutation['dit_exit'])
        if (len(parameters['deltatheta_exit']) > 1): strategy_code += '_DT_' + str(permutation['deltatheta_exit'])
        code_tp = permutation['tp_exit']
        if (code_tp is not None) and code_tp < 1: 
            code_tp = int(code_tp * 100)
        if (len(parameters['tp_exit']) > 1): strategy_code += '_P' + str(code_tp)
        if (len(parameters['sl_exit']) > 1): strategy_code += '_L' + str(permutation['sl_exit'])
        if (len(parameters['delta']) > 1): strategy_code += '_D_' + str(permutation['delta'])
        
        if strategy_code == '': 
            strategy_code = 'X'
        if strategy_code.startswith('_'): 
            strategy_code = strategy_code[1:]
        strategy_code = strategy_code.replace('None', 'X')
    
        if (strategy_name == 'bf70' or strategy_name == 'bf70_plus') and (permutation['cheap_entry'] == None) and (permutation['down_day_entry'] == False) and (permutation['patient_entry'] == True): 
            if printalot: print('continue')
            continue

        number_of_trades = 0
        winners = 0 
        allwinners = 0
        allloosers = 0
        maxwinner = 0 
        loosers = 0
        maxlooser = 0 
        total_pnl = 0
        total_risk = 0
        exits = {}
        total_dit = 0
        total_daily_pnls = None 
        total = risk_capital
        total_positions = 0
        
        running_global_peak = 0
        running_global_peak_date = datetime(2000, 1, 1).date()
        max_dd = 0 
        running_max_dd_date = datetime(2000, 1, 1).date()

        # measure time to get entries 
        starttiming = time.time()
        if daily: 
            single_entries = entries.getDailyEntries(underlying, start, end, permutation['dte_entry'])
        else: 
            single_entries = entries.getEntries(underlying, start, end, permutation['dte_entry'], True, False)
        endtiming = time.time()
        print('time needed to get single entries: ' + str(endtiming - starttiming))

        for e in range(len(single_entries)): 
        
            entry = single_entries[e]
            entrydate = entry[0]
            expiration = entry[1]

            if entrydate >= (datetime.now().date() - timedelta(days=7)):
                break 
            
            if strategy_name == 'the_bull': 
                permutation['dte_exit'] = 37
                try: 
                    next_entry = single_entries[e + 1]
                    next_entrydate = next_entry[0]
                    permutation['dte_exit'] = 66 - (next_entrydate - entrydate).days
                except IndexError: 
                    continue
                
            strategy.setParameters(permutation['patient_days_before'], permutation['patient_days_after'], permutation['cheap_entry'], permutation['down_day_entry'], permutation['patient_entry'], permutation['min_vix_entry'], permutation['max_vix_entry'], permutation['dte_entry'], permutation['els_entry'], permutation['ew_exit'], permutation['pct_exit'], permutation['dte_exit'], permutation['dit_exit'], permutation['deltatheta_exit'], permutation['tp_exit'], permutation['sl_exit'], permutation['delta'])
            result = run_strategies.fly(strategy, underlying, risk_capital, entrydate, expiration)
            

            if (not result is None): 
                number_of_trades += 1
                i += 1
                
                # save dailypnls 
                file_name = strategy_path + '/daily_pnls/' + strategy_code + '_' + str(i) + '.csv'
                result['dailypnls'].to_csv(file_name)
                del result['dailypnls']

                trade_log[i] = dict({'trade nr.' : number_of_trades, 'strategy_code': strategy_code}, **result)
                print (trade_log[i])


                # TODO/GOAL: get all of this out of this loop 
                total_positions += int(trade_log[i]['position_size'])
                
                total_risk += trade_log[i]['max_risk']
                total_pnl += trade_log[i]['pnl'] 
                if trade_log[i]['pnl']  >= 0: 
                    allwinners += trade_log[i]['pnl'] 
                    winners += 1
                    if trade_log[i]['pnl']  > maxwinner: 
                        maxwinner = trade_log[i]['pnl']  

                else: 
                    allloosers += trade_log[i]['pnl'] 
                    loosers += 1 
                    if trade_log[i]['pnl'] < maxlooser: 
                        maxlooser = trade_log[i]['pnl'] 

                total_dit += trade_log[i]['dit']

                if trade_log[i]['exit'] in exits: 
                    exits[trade_log[i]['exit']] += 1
                else:
                    exits[trade_log[i]['exit']] = 1


        # merge all total_daily_pnls
        for filename in os.listdir(strategy_path + '/daily_pnls'):
            if filename.endswith('.csv'):
                
                daily_pnls = pd.read_csv(strategy_path + '/daily_pnls/' + filename, parse_dates=['date'], index_col=['date'])

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
            equity_curve[j] = [strategy_code, key.date(), int(total)]
                             
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
        average_position_size = total_positions / number_of_trades
        rod = round((average_percentage / (total_dit / number_of_trades)), 2)

        if printalot: print()
        for key, value in exits.items():
            if printalot: print(key + ' exit: \t' + str(value))
            
        days = (end - start).days
        years = round((days / 365), 2)
        
        annualized_pnl = int(total_pnl) / years 
        annualized_RoR = round((annualized_pnl / risk_capital * 100), 2)
        
        rrr = round((annualized_RoR / -max_dd_risk_percentage), 2)

        results_table[strategy_code] = [number_of_trades, annualized_sharpe_ratio, annualized_sortino_ratio, int(total_pnl), average_pnl, average_risk, average_percentage, annualized_RoR, max_dd, max_dd_risk_percentage, max_dd_percentage, running_max_dd_date.date(), max_dd_duration, percentage_winners, average_winner, int(maxwinner), average_looser, int(maxlooser), average_dit, average_position_size, rod, rrr] 


    # finished looping through permutations 
    df_log = pd.DataFrame.from_dict(trade_log, orient='index')
    df_log.to_csv(strategy_path + '/single_results.csv')
    
    df_curve = pd.DataFrame(data=equity_curve, index=['strategy', 'date', 'pnl']).T
    df_curve.to_csv(strategy_path + '/results.csv')
    
    df_table = pd.DataFrame(data=results_table, index=['trades', 'Sharpe', 'Sortino', 'total pnl', 'avg pnl', 'avg risk', 'avg RoR %', 'annualized RoR%', 'max dd $', 'max dd on risk %', 'max dd on previous peak %', 'max dd date', 'max dd duration', 'pct winners', 'avg winner', 'max winner', 'avg looser', 'max looser', 'avg DIT', 'avg size', 'avg RoR / avg DIT', 'RRR'])
    df_table.to_html(strategy_path + '/results_table.html')
    print(df_table)

    # Copy files
    shutil.copyfile(path + '/util/web/d3.js', strategy_path + '/d3.js') 
    shutil.copyfile(path + '/util/web/index.html', strategy_path + '/index.html') 
    try:
        shutil.copyfile(path + '/util/web/' + str(strategy_name) + '.html', strategy_path + '/strategy.html') 
    except Exception as e:
        print(e)
