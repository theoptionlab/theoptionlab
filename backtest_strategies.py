# -*- coding: utf-8 -*-
from __future__ import division

import collections
from datetime import datetime
from datetime import timedelta 
import itertools
import os 
import shutil 

import numpy as np
import pandas as pd
import run_strategies
from util import entries
from util import performance


def dict_product(d):
    keys = d.keys()
    for element in itertools.product(*d.values()):
        yield dict(zip(keys, element))
        
        
def backtest(strategy, strategy_flavor, risk_capital, printalot, start, end, parameters): 
    
    if printalot: print("strategy_name_extra: " + str(strategy_flavor))
    if printalot: print("risk_capital: " + str(risk_capital))
    if printalot: print("underlying: " + str(strategy.underlying))
    if printalot: print("start: " + str(start))
    if printalot: print("end: " + str(end))
    if printalot: print()

    permutations = dict_product(parameters)
    if printalot: print("number of combinations: " + str(len(list(permutations))))

    trade_log = collections.OrderedDict()
    equity_curve = collections.OrderedDict()
    results_table = collections.OrderedDict()
    
    i = 0 
    j = 0 
    
    permutations = dict_product(parameters)
    for permutation in  permutations: 
        for k, v in permutation.items(): 
            if printalot: print(k, v)
        
        strategy_code = "" 

        if permutation['cheap_entry'] is not None: strategy_code += "C"
        if ((len(parameters["down_day_entry"]) > 1) and permutation['down_day_entry']): strategy_code += "D"
        if ((len(parameters["patient_entry"]) > 1) and permutation['patient_entry']): strategy_code += "P"
        if ((len(parameters["ew_exit"]) > 1) and permutation['ew_exit']): strategy_code += "E"
        if permutation['min_vix_entry'] is not None: strategy_code += "_MIV_" + str(permutation['min_vix_entry'])
        if permutation['max_vix_entry'] is not None: strategy_code += "_MAV_" + str(permutation['max_vix_entry'])
        if (len(parameters["dte_entry"]) > 1): strategy_code += "_E" + str(permutation['dte_entry'])
        if permutation['els_entry'] is not None: strategy_code += "_EE_" + str(permutation['els_entry'])
        if permutation['pct_exit'] is not None: strategy_code += "_C" + str(int(permutation['pct_exit'] * 100))
        if ((len(parameters["dte_exit"]) > 1) and permutation['dte_exit'] != 0): strategy_code += "_X" + str(permutation['dte_exit'])
        if ((len(parameters["dit_exit"]) > 1) and permutation['dit_exit'] != 0): strategy_code += "_EXDIT_" + str(permutation['dit_exit'])
        if (len(parameters["deltatheta_exit"]) > 1): strategy_code += "_DT_" + str(permutation['deltatheta_exit'])
        code_tp = permutation['tp_exit']
        if (code_tp is not None) and code_tp < 1: 
            code_tp = int(code_tp * 100)
        if (len(parameters["tp_exit"]) > 1): strategy_code += "_P" + str(code_tp)
        if (len(parameters["sl_exit"]) > 1): strategy_code += "_L" + str(permutation['sl_exit'])
        if (len(parameters["delta"]) > 1): strategy_code += "_D_" + str(permutation['delta'])
        
        if strategy_code == "": 
            strategy_code = "X"
        if strategy_code.startswith("_"): 
            strategy_code = strategy_code[1:]
        strategy_code = strategy_code.replace("None", "X")
    
        if (strategy.name == "bf70" or strategy.name == "bf70_plus") and (permutation['cheap_entry'] == None) and (permutation['down_day_entry'] == False) and (permutation['patient_entry'] == True): 
            if printalot: print("continue")
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

        single_entries = entries.getEntries(strategy.connector, strategy.underlying, start, end, permutation['dte_entry'], True, False)
        
        for e in range(len(single_entries)): 
            
            entry = single_entries[e]
                                
            if entry['entrydate'] >= (datetime.now().date() - timedelta(days=7)):
                break 
            
            if strategy.name == "the_bull": 
                permutation['dte_exit'] = 37
                try: 
                    next_entry = single_entries[e + 1]
                    permutation['dte_exit'] = 66 - (next_entry['entrydate'] - entry['entrydate']).days
                except IndexError: 
                    continue
                
            strategy.setParameters(permutation['cheap_entry'], permutation['down_day_entry'], permutation['patient_entry'], permutation['min_vix_entry'], permutation['max_vix_entry'], permutation['dte_entry'], permutation['els_entry'], permutation['ew_exit'], permutation['pct_exit'], permutation['dte_exit'], permutation['dit_exit'], permutation['deltatheta_exit'], permutation['tp_exit'], permutation['sl_exit'], permutation['delta'])
            result = run_strategies.fly(strategy, risk_capital, entry['entrydate'], entry['expiration'])
            
            if (not result is None): 
                number_of_trades += 1
                i += 1
    
                daily_pnls = pd.DataFrame.from_dict(result['dailypnls'], orient='index')
                daily_pnls = daily_pnls.reindex(daily_pnls.index.rename('date'))
                daily_pnls.index = pd.to_datetime(daily_pnls.index)
                daily_pnls.sort_index(inplace=True)
                daily_pnls.columns = ['pnl']
                
                if (total_daily_pnls is None): 
                    total_daily_pnls = daily_pnls
                    
                else: 
                    total_daily_pnls = pd.concat([daily_pnls, total_daily_pnls], axis=0, join='outer', ignore_index=False).groupby(["date"], as_index=True).sum()
                    total_daily_pnls.sort_index(inplace=True)
    
                pnl = result['pnl'] 
                percentage = round((int(pnl) / abs(result['max_risk'])) * 100, 2)
                
                trade_log[i] = [strategy_code, number_of_trades, entry['expiration'], result['entry_date'], result['strikes'], round(result['entry_price'], 2), result['exit_date'], result['dit'], result['dte'], int(pnl), int(result['max_risk']), int(result['position_size']), str(percentage) + '%', result['exit']]
                print(trade_log[i])
                
                total_positions += int(result['position_size'])
                
                total_risk += result['max_risk']
                total_pnl += pnl
                if pnl >= 0: 
                    allwinners += pnl
                    winners += 1
                    if pnl > maxwinner: 
                        maxwinner = pnl 
                          
                else: 
                    allloosers += pnl
                    loosers += 1 
                    if pnl < maxlooser: 
                        maxlooser = pnl
                        
                total_dit += result['dit']
                
                if result['exit'] in exits: 
                    exits[result['exit']] += 1
                else:
                    exits[result['exit']] = 1
    
        if (total_daily_pnls is None): 
            print("no trades")
            continue 
        
        total_daily_pnls['cum_sum'] = total_daily_pnls.pnl.cumsum() + total
        total_daily_pnls['daily_ret'] = total_daily_pnls['cum_sum'].pct_change()
    
        annualized_sharpe_ratio = performance.annualized_sharpe_ratio(np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)
        annualized_sortino_ratio = performance.sortino_ratio(np.mean(total_daily_pnls['daily_ret']), total_daily_pnls['daily_ret'], 0)
        
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

        if printalot: print 
        for key, value in exits.items():
            if printalot: print(key + " exit: \t" + str(value))
        print () 
            
        days = (end - start).days
        years = round((days / 365), 2)
        
        annualized_pnl = int(total_pnl) / years 
        annualized_RoR = round((annualized_pnl / risk_capital * 100), 2)
        
        rrr = round((annualized_RoR / -max_dd_risk_percentage), 2)

        results_table[strategy_code] = [number_of_trades, annualized_sharpe_ratio, annualized_sortino_ratio, int(total_pnl), average_pnl, average_risk, average_percentage, annualized_RoR, max_dd, max_dd_risk_percentage, max_dd_percentage, running_max_dd_date.date(), max_dd_duration, percentage_winners, average_winner, int(maxwinner), average_looser, int(maxlooser), average_dit, average_position_size, rod, rrr] 

    path = os.getcwd()
    print ("The current working directory is %s" % path)

    results_path = path + "/results" 
    try:
        os.mkdir(results_path)
    except OSError:
        print ("Creation of the directory %s failed" % results_path)
    else:
        print ("Successfully created the directory %s " % results_path)

    strategy_path = path + "/results/" + strategy.name 

    try:
        os.mkdir(strategy_path)
    except OSError:
        print ("Creation of the directory %s failed" % strategy_path)
    else:
        print ("Successfully created the directory %s " % strategy_path)

    df_log = pd.DataFrame(data=trade_log, index=["strategy_code", "trade nr.", "expiration", "entry_date", "strikes", "entry_price", "exit_date", "DIT", "DTE", "pnl", "max risk", "position size", "percentage", "exit"]).T
    df_log.to_csv(strategy_path + "/single_results.csv")
    
    df_curve = pd.DataFrame(data=equity_curve, index=["strategy", "date", "pnl"]).T
    df_curve.to_csv(strategy_path + "/results.csv")
    
    df_table = pd.DataFrame(data=results_table, index=["trades", "Sharpe", "Sortino", "total pnl", "avg pnl", "avg risk", "avg RoR %", "annualized RoR%", "max dd $", "max dd on risk %", "max dd on capital %", "max dd date", "max dd duration", "pct winners", "avg winner", "max winner", "avg looser", "max looser", "avg DIT", "avg size", "avg RoR / avg DIT", "RRR"])
    df_table.to_html(strategy_path + "/results_table.html")
    print(df_table)

    # Copy files
    shutil.copyfile(path + "/util/web/d3.js", strategy_path + "/d3.js") 
    shutil.copyfile(path + "/util/web/index.html", strategy_path + "/index.html") 
    shutil.copyfile(path + "/util/web/" + str(strategy.name) + ".html", strategy_path + "/strategy.html") 
    
