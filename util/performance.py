import math 

import numpy as np


# def sharpe_ratio(returns):
#     """
#     Create the Sharpe ratio for the strategy, based on a 
#     benchmark of zero (i.e. no risk-free rate information).
# 
#     Parameters:
#     returns - A pandas Series representing period percentage returns.
#     """
#     return np.sqrt(returns.length()) * (np.mean(returns)) / np.std(returns)
# http://www.turingfinance.com/computational-investing-with-python-week-one/
def sharpe_ratio(er, returns, rf):
    return (er - rf) / np.std(returns)


def annualized_sharpe_ratio(er, returns, rf): 
    sr = sharpe_ratio(er, returns, rf)
    annualized_sharpe_ratio = round((np.sqrt(252) * sr), 2)
    return annualized_sharpe_ratio


def sortino_ratio(er, returns, rf, target=0):
    return (er - rf) / math.sqrt(lpm(returns, target, 2)) if math.sqrt(lpm(returns, target, 2)) else 0


def annualized_sortino_ratio(er, returns, rf, target=0):
    sr = sortino_ratio(er, returns, rf, target=0) 
    annualized_sortino_ratio = round((np.sqrt(252) * sr), 2)
    return annualized_sortino_ratio


# This method returns a lower partial moment of the returns
# Create an array he same length as returns containing the minimum return threshold
def lpm(returns, threshold, order):
    threshold_array = np.empty(len(returns))
    threshold_array.fill(threshold)
    # Calculate the difference between the threshold and the returns
    diff = threshold_array - returns
    # Set the minimum of each to 0
    # diff = diff.clip(min=0)
    diff = diff.clip(0)
    # Return the sum of the different to the power of order
    return np.sum(diff ** order) / len(returns)
