# -*- coding: utf-8 -*-
from __future__ import division

from datetime import datetime
from datetime import timedelta 
import itertools
import os 
import shutil 
import time

import pandas as pd

import run_strategy

from util import util
from util import entries

import trading_calendars as tc
import pytz
xnys = tc.get_calendar("XNYS")


def dict_product(d):
    keys = d.keys()
    for element in itertools.product(*d.values()):
        yield dict(zip(keys, element))


def make_dir(path): 
    try:
        os.mkdir(path)
    except OSError:
        print ('Creating dir %s failed' % path)
    else:
        print ('Created dir %s ' % path)


def get_next_entry (index_nr, frequency_string, single_entries, entry_date, end_date, underlying, dte): 
    

    if frequency_string == 'C': 
        entries = {}

        while (entry_date <= end_date):

            expiration = util.connector.select_expiration(entry_date, underlying, "p", dte)
            if expiration is None: 
                entry_date = entry_date + timedelta(days=1)
                continue 

            else: 
                entries[entry_date] = expiration
                return list(entries.items())[0]

    else:
        if index_nr < len(single_entries): 
            return single_entries[index_nr]

    return None 



def run_strategies(permutations, strategy_name, parameters, strategy_path, frequency_string, underlying, start, end, strategy, risk_capital, quantity, include_underlying = False): 
    
    trade_log = {}
    i = 0 

    for permutation in permutations: 
        
        running = True 
        
        for k, v in permutation.items(): 
            if util.printalot: print(k, v)

        if (strategy_name == 'bf70' or strategy_name == 'bf70_plus') and (permutation['cheap_entry'] == None) and (permutation['down_day_entry'] == False) and (permutation['patient_entry'] == True): 
            if util.printalot: print('continue')
            continue
        
        strategy_code = util.derive_strategy_code(permutation, parameters)
        print (strategy_code)

        # make dir for permutation 
        strategy_code_path = strategy_path + '/daily_pnls/' + strategy_code + "/"
        make_dir(strategy_code_path)

        single_entries = {}
        # get entries, measure time 
        starttime = time.time()
        if frequency_string == 'C': 
            single_entries = {} 
        if frequency_string == 'B': 
            single_entries = entries.getDailyEntries(underlying, start, end, permutation['dte_entry'])
        if frequency_string == 'SMS': 
            single_entries = entries.getSMSEntries(underlying, start, end, permutation['dte_entry'])
        if frequency_string is None: 
            single_entries = entries.getEntries(underlying, start, end, permutation['dte_entry'])

        print('time needed to get entries: ' + format(float(time.time() - starttime), '.2f'))
        

        # loop through entries 
        trade_nr = 0
        index_nr = 0 
        next_date = None 
        
        while (running): 

            if next_date is None: next_date = start 
            entry = get_next_entry(index_nr, frequency_string, single_entries, next_date, end, underlying, permutation['dte_entry']) 
            
            if entry is not None: 
                entrydate = entry[0]
                expiration = entry[1]
    
                if entrydate >= (datetime.now().date() - timedelta(days=7)):
                    break 
                
                if strategy_name == 'the_bull': 
                    permutation['dte_exit'] = 37
                    try: 
                        next_entry = get_next_entry(index_nr + 1, frequency_string, single_entries, next_date, end, underlying, permutation['dte_entry']) 
                        if next_entry is not None: 
                            permutation['dte_exit'] = 66 - (next_entry[0] - entrydate).days
                    except Exception as e:
                        print (e)
                    
                # run with parameters 
                strategy.setParameters(permutation['patient_days_before'], 
                permutation['patient_days_after'], 
                permutation['cheap_entry'], 
                permutation['down_day_entry'], 
                permutation['patient_entry'], 
                permutation['min_vix_entry'], 
                permutation['max_vix_entry'], 
                permutation['min_iv_entry'], 
                permutation['max_iv_entry'], 
                permutation['sma_window'], 
                permutation['dte_entry'], 
                permutation['els_entry'], 
                permutation['ew_exit'], 
                permutation['pct_exit'], 
                permutation['dte_exit'], 
                permutation['dit_exit'], 
                permutation['deltatheta_exit'], 
                permutation['tp_exit'], 
                permutation['sl_exit'], 
                permutation['delta'])
                result = run_strategy.fly(strategy, underlying, risk_capital, quantity, entrydate, expiration)

                if (not result is None): 
                    trade_nr += 1
                    i += 1
    
                    # save dailypnls 
                    file_name = strategy_code_path + str(i) + '.csv'
                    result['dailypnls'].to_csv(file_name)
                    del result['dailypnls']
    
                    trade_log[i] = dict({'trade nr.' : trade_nr, 'strategy_code': strategy_code}, **result)
                    print (trade_log[i])
                    next_date = (result["exit_date"]) + timedelta(days=1)

                else: next_date = next_date + timedelta(days=1)
                    
                index_nr += 1 
            
            else: running = False 


    if (include_underlying): 
        # create results file for underlying   
        underlying_daily_pnls_dict = {}
        underlying_date = start
        underlying_multiplier = None 
        underlying_at_entry = None
        entry_vix = None 
        previouspnl = 0 
        
        while (underlying_date <= end):
        
            while ((xnys.is_session(pd.Timestamp(underlying_date, tz=pytz.UTC)) is False) 
                   or (util.connector.query_midprice_underlying(underlying, underlying_date) is None)): 
                   
                underlying_date = underlying_date + timedelta(days=1)
                if (underlying_date >= end) or (underlying_date >= datetime.now().date()): 
                    break
                    
            underlying_midprice = util.connector.query_midprice_underlying(underlying, underlying_date)
            if underlying_midprice != 0: 
            
                if underlying_multiplier is None:
                    underlying_start_date = underlying_date
                    underlying_at_entry = underlying_midprice
                    underlying_multiplier = (risk_capital / underlying_midprice)
                    entry_vix = util.connector.query_midprice_underlying("^VIX", underlying_date) 
                
                
                current_pnl = (underlying_multiplier * underlying_midprice) - risk_capital
                if current_pnl != None:             
                    underlying_daily_pnls_dict[underlying_date] = format(float(current_pnl - previouspnl), '.2f') 
                    previouspnl = current_pnl
                    
            underlying_date = underlying_date + timedelta(days=1)
            
            
        underlying_daily_pnls = pd.DataFrame.from_dict(underlying_daily_pnls_dict, orient='index')
        underlying_daily_pnls = underlying_daily_pnls.reindex(underlying_daily_pnls.index.rename('date'))
        underlying_daily_pnls.index = pd.to_datetime(underlying_daily_pnls.index)
        underlying_daily_pnls.sort_index(inplace=True)
        underlying_daily_pnls.columns = ['pnl']
        
        underlying_strategy_code_path = strategy_path + '/daily_pnls/' + str(underlying.replace("^","")) + "/"
        make_dir(underlying_strategy_code_path)
        underlying_file_name = underlying_strategy_code_path + 'underlying.csv'
        underlying_daily_pnls.to_csv(underlying_file_name)
        
        # save underlying to trade_log
        trade_log[i+1] = dict({'trade nr.' : trade_nr+1, 'strategy_code': str(underlying.replace("^","")), 'entry_date': underlying_start_date, 'expiration': None, 'exit_date': underlying_date, 'entry_underlying': str(format(float(underlying_at_entry), '.2f')), 'entry_vix': entry_vix, 'strikes': None, 'iv_legs': None, 'entry_price': str(format(float(risk_capital), '.2f')), 'dte' : 0, 'dit' : (end - start).days, 'pnl': str(format(float(current_pnl), '.2f')), 'dailypnls' : None, 'max_risk' : str(format(float(risk_capital), '.2f')), 'position_size' : underlying_multiplier, 'percentage': str(format(float(round((float(current_pnl) / risk_capital) * 100, 2)), '.2f')) + '%', 'exit': None})

    # finished looping, save trade_log 
    df_log = pd.DataFrame.from_dict(trade_log, orient='index')
    df_log.to_csv(strategy_path + '/single_results.csv')
        
        
def backtest(strategy, underlying, strategy_name, risk_capital, quantity, start, end, parameters, frequency_string=None, include_underlying=False): 

    if util.printalot: print ('strategy_name: ' + str(strategy_name))
    if util.printalot: print ('risk_capital: ' + str(risk_capital))
    if util.printalot: print ('underlying: ' + str(underlying))
    if util.printalot: print ('start: ' + str(start))
    if util.printalot: print ('end: ' + str(end))
    if util.printalot: print ()
    
    # prepare 
    if util.printalot: print('number of combinations: ' + str(len(list(dict_product(parameters)))))
    permutations = dict_product(parameters)
        
    # create directories  
    path = os.getcwd()
    make_dir(path + '/results')
    strategy_path = path + '/results/' + strategy_name 
    if frequency_string == "B": strategy_path += '_daily'
    make_dir(strategy_path)
    try: 
        shutil.rmtree(strategy_path + '/daily_pnls')
    except Exception as e:
        print(e)
    make_dir(strategy_path + '/daily_pnls')
    
    run_strategies(permutations, strategy_name, parameters, strategy_path, frequency_string, underlying, start, end, strategy, risk_capital, quantity, include_underlying)

