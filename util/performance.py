import numpy as np
import math 


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

def sortino_ratio(er, returns, rf, target=0):
    return (er - rf) / math.sqrt(lpm(returns, target, 2))



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
