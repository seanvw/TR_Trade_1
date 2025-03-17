#!python3
#from sharedeal import *
from portfolio import * 


portfolio = Portfolio(owner='SW', platform='Trade Republic', verbose_reporting=False)
# Current transaction cost for a sale or buy
tc_eur = 1.00

# 2023/10
year = 2023
month = 10
portfolio.add_share(ticker='AAPL', buy_price=160, quantity=1.5, buy_datetime=datetime(year, month, 1, 9, 30), transaction_cost_eur=tc_eur)
portfolio.add_share(ticker='AAPL', buy_price=200, quantity=1.5, buy_datetime=datetime(year, month, 2, 10, 30), transaction_cost_eur=tc_eur)

# 2023/11
month = 11
portfolio.sell_share(ticker='AAPL', sell_price=240, quantity=1.0, tax=15, sell_datetime=datetime(year, month, 1, 14, 30), transaction_cost_eur=tc_eur)
portfolio.sell_share(ticker='AAPL', sell_price=240, quantity=1.0, tax=15, sell_datetime=datetime(year, month, 2, 18, 30), transaction_cost_eur=tc_eur)

# 2023/12 
month = 12
portfolio.add_share(ticker='GOOG', buy_price=100.0, quantity=10, buy_datetime=datetime(year, month, 2, 10, 30), transaction_cost_eur=tc_eur)

print(portfolio)

