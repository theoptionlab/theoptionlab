# -*- coding: utf-8 -*-
from __future__ import division
from util import performance
import itertools
import run_strategies
from util import entries
from datetime import datetime
from datetime import timedelta 
import numpy as np
import pandas as pd
import collections

def backtest(strategy, strategy_flavor, risk_capital, printalot, start, end, parameters): 
    
    if printalot: print("strategy_name_extra: " + str(strategy_flavor))
    if printalot: print("risk_capital: " + str(risk_capital))
    if printalot: print("underlying: " + str(strategy.underlying))
    if printalot: print("start: " + str(start))
    if printalot: print("end: " + str(end))
    if printalot: print()
    
    
    s = []
    for parameter_name, parameter in parameters.items(): 
        if parameter is not [None]:
            s.append(parameter)
        else: s.append(None) 

    if printalot: print("number of combinations: " + str(len(list(itertools.product(*s)))))
    if printalot: print()


    trade_log = collections.OrderedDict()
    equity_curve = collections.OrderedDict()
    results_table = collections.OrderedDict()
    
    i = 0 
    j = 0 
    
    
    for combination in list(itertools.product(*s)):

        cheap_entry = combination[0]
        down_day_entry = combination[1]
        patient_entry = combination[2]
        min_vix_entry = combination[3]
        max_vix_entry = combination[4]
        dte_entry = combination[5]
        els_entry  = combination[6]
        ew_exit = combination[7]
        pct_exit = combination[8]
        dte_exit = combination[9]
        dit_exit = combination[10]
        deltatheta_exit = combination[11]
        tp_exit = combination[12]
        sl_exit = combination[13]
        delta = combination[14]


        if printalot: print("cheap_entry: " + str(cheap_entry))
        if printalot: print("down_day_entry: " + str(down_day_entry))
        if printalot: print("patient_entry: " + str(patient_entry))
        if printalot: print("min_vix_entry: " + str(min_vix_entry))
        if printalot: print("max_vix_entry: " + str(max_vix_entry))
        if printalot: print("dte_entry: " + str(dte_entry))
        if printalot: print("els_entry: " + str(els_entry))
        if printalot: print("ew_exit: " + str(ew_exit))
        if printalot: print("pct_exit: " + str(pct_exit))
        if printalot: print("dte_exit: " + str(dte_exit))
        if printalot: print("dit_exit: " + str(dit_exit))
        if printalot: print("deltatheta_exit: " + str(deltatheta_exit))
        if printalot: print("tp_exit: " + str(tp_exit))
        if printalot: print("sl_exit: " + str(sl_exit))
        if printalot: print("delta: " + str(delta))
        if printalot: print()
    
    
        strategy_code = "" 

        if cheap_entry is not None: strategy_code += "C"
        if ((len(parameters["down_day_entry"]) > 1) and down_day_entry): strategy_code += "D"
        if ((len(parameters["patient_entry"]) > 1) and patient_entry): strategy_code += "P"
        if ((len(parameters["ew_exit"]) > 1) and ew_exit): strategy_code += "E"
        if min_vix_entry is not None: strategy_code += "_MIV_" + str(min_vix_entry)
        if max_vix_entry is not None: strategy_code += "_MAV_" + str(max_vix_entry)
        if (len(parameters["dte_entry"]) > 1): strategy_code += "_DTE_" + str(dte_entry)
        if els_entry is not None: strategy_code += "_EE_" + str(els_entry)
        if pct_exit is not None: strategy_code += "_DC_" + str(int(pct_exit * 100))
        if ((len(parameters["dte_exit"]) > 1) and dte_exit != 0): strategy_code += "_EXDTE_" + str(dte_exit)
        if ((len(parameters["dit_exit"]) > 1) and dit_exit != 0): strategy_code += "_EXDIT_" + str(dit_exit)
        if (len(parameters["deltatheta_exit"]) > 1): strategy_code += "_DTR_" + str(deltatheta_exit)
        if (len(parameters["tp_exit"]) > 1): strategy_code += "_TP_" + str(tp_exit) 
        if (len(parameters["sl_exit"]) > 1): strategy_code += "_SL_" + str(sl_exit)
        if (len(parameters["delta"]) > 1): strategy_code += "_D_" + str(delta)
    
        
        if strategy_code == "": 
            strategy_code = "X"
        if strategy_code.startswith("_"): 
            strategy_code = strategy_code[1:]
        strategy_code = strategy_code.replace("None", "X")

    
        if (strategy.name =="bf70" or strategy.name == "bf70_plus") and (cheap_entry == None) and (down_day_entry == False) and (patient_entry == True): 
            if printalot: print("continue")
            continue
        

        trade_nr = 0
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
        total = 200000
        total_positions = 0
        
        running_global_peak = 0
        running_global_peak_date = datetime(2000, 1, 1).date()
        max_dd = 0 
        running_max_dd_date = datetime(2000, 1, 1).date()

        
        single_entries = entries.getEntries(strategy.connector, strategy.underlying, start, end, dte_entry, True, False)
                
        for e in range(len(single_entries)): 
            entry = single_entries[e]
                                
            if entry['entrydate'] >= (datetime.now().date() - timedelta(days=7)):
                break 
            
            if strategy.name == "the_bull": 
                dte_exit = 37
                try: 
                    next_entry = single_entries[e+1]
                    dte_exit = 66 - (next_entry['entrydate'] - entry['entrydate']).days
                except IndexError: 
                    continue
                
                
            strategy.setParameters(cheap_entry, down_day_entry, patient_entry, min_vix_entry, max_vix_entry, dte_entry, els_entry, ew_exit, pct_exit, dte_exit, dit_exit, deltatheta_exit, tp_exit, sl_exit, delta)
#             print(entry['entrydate'])
            result = run_strategies.fly(strategy, risk_capital, entry['entrydate'], entry['expiration'])
                
            if (not result is None): 
                trade_nr += 1
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
                
                trade_log[i] = [strategy_code, trade_nr, entry['expiration'], result['entry_date'], result['strikes'], round(result['entry_price'],2), result['exit_date'], result['dit'], result['dte'], int(pnl), int(result['max_risk']), int(result['position_size']), str(percentage) + '%', result['exit']]
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
            j+=1
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
                    max_dd_percentage = round((max_dd / running_global_peak * 100),2)  
                    max_dd_risk_percentage = round((max_dd / 100000 * 100),2)  
                    max_dd_duration = abs((running_global_peak_date - running_max_dd_date).days)
            
        
        average_pnl = int(total_pnl / trade_nr)
        average_risk = int(total_risk / trade_nr)
        average_percentage = round(total_pnl / abs(total_risk) * 100, 2)
        percentage_winners = int((winners / trade_nr) * 100)

        try: 
            average_winner = int(allwinners/winners)
        except ZeroDivisionError:
            average_winner = 0
            
        try: 
            average_looser = int(allloosers/(trade_nr-winners))
        except ZeroDivisionError:
            average_looser = 0
            
        average_dit = int(total_dit / trade_nr)
        average_position_size = total_positions / trade_nr
        rod = round((average_percentage / (total_dit / trade_nr)),2)

        if printalot: print 
        for key, value in exits.items():
            if printalot: print(key + " exit: \t" + str(value))
            
        days = (end - start).days
        years = round((days / 365),2)
        
        annualized_pnl = int(total_pnl) / years 
        annualized_RoR = round((annualized_pnl / 100000 * 100),2)
        
        rrr = round((annualized_RoR / -max_dd_risk_percentage),2)
        

        results_table[strategy_code] = [trade_nr, annualized_sharpe_ratio, annualized_sortino_ratio, int(total_pnl), average_pnl, average_risk, average_percentage, annualized_RoR, max_dd, max_dd_risk_percentage, max_dd_percentage, running_max_dd_date.date(), max_dd_duration, percentage_winners, average_winner, int(maxwinner), average_looser, int(maxlooser), average_dit, average_position_size, rod, rrr] 

    df_table = pd.DataFrame(data=results_table, index = ["trades", "Sharpe", "Sortino", "total pnl", "avg pnl", "avg risk", "avg RoR %", "annualized RoR%", "max dd $", "max dd on risk %", "max dd on capital %", "max dd date", "max dd duration", "pct winners", "avg winner", "max winner", "avg looser", "max looser", "avg DIT", "avg size", "avg RoR / avg DIT", "RRR"])
    df_table.to_html("results/" + strategy.name + "_results_table.html")
        
    df_curve = pd.DataFrame(data=equity_curve, index = ["strategy","date","pnl"]).T
    df_curve.to_csv("results/" + strategy.name + "_results.csv")
    
    df_log = pd.DataFrame(data=trade_log, index = ["strategy_code","trade nr.","expiration", "entry_date", "strikes", "entry_price", "exit_date", "DIT", "DTE", "pnl", "max risk", "position size", "percentage", "exit"]).T
    df_log.to_csv("results/" + strategy.name + "_single_results.csv")

    print(df_table)
    