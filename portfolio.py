#!python3
from functools import cached_property
from datetime import datetime
from dataclasses import dataclass
import yfinance as yf
import statistics
import re
from sharedeal import *

@dataclass
class ExchangeRate_current_usd_eur():

  def __post_init__(self):
        stock = yf.Ticker("USDEUR=X")
        self.current_usd_eur = stock.info['regularMarketPrice']

  def get_current_usd_eur(self):
    return self.current_usd_eur


@dataclass
class Portfolio():
    owner: str
    platform: str
    verbose_reporting: bool


    def __post_init__(self):
        self.shares = {}

    def __str__(self) -> str:
      self.generate_report(verbose=self.verbose_reporting)
      return ""

    def add_share(self, ticker, buy_price, quantity, buy_datetime, transaction_cost_eur):
        
        if (transaction_cost_eur < 0):
          raise ValueError(f"Transaction cost cannot be negative: {transaction_cost_eur}")
        if (quantity < 0):
          raise ValueError(f"Quantity cannot be negative: {quantity}")
        if (buy_price < 0):
          raise ValueError(f"Buy price cannot be negative: {buy_price}")
        dt_now = datetime.now().replace(microsecond=0)
        if (buy_datetime > dt_now):
          raise ValueError(f"Buy date cannot be in the future: {buy_datetime} Now: {dt_now}")
        if (quantity == 0): 
          raise ValueError(f"Quantity cannot be zero: {quantity}")
        if (buy_price == 0):
          raise ValueError(f"Buy price cannot be zero: {buy_price}")

        if ticker in self.shares:
          #print(f"Ticker {ticker} found in portfolio.")
          share = self.shares[ticker]
        else:
          #print(f"Ticker {ticker} not found in portfolio. Creating new share.")
          # get the current exchange rate as it needed as stock price served in USD with yfinance
          current_usd_eur = ExchangeRate_current_usd_eur().get_current_usd_eur()
          share = Share(ticker,current_usd_eur)
          self.shares[ticker] = share
        print(f"Accounting for Share purchase: {quantity} {ticker} at {buy_price: .2f} on {buy_datetime} with fee of {transaction_cost_eur}")
        share.add_transaction(buy_price, quantity, buy_datetime, transaction_cost_eur)


    def sell_share(self, ticker, sell_price, quantity, tax, sell_datetime, transaction_cost_eur):
        if ticker in self.shares:
          share = self.shares[ticker]
          #print(f"sell_share, Ticker {ticker} found in portfolio.")
          share.sell_transaction(sell_price, quantity, tax, sell_datetime, transaction_cost_eur)
          print(f"Accounting for Share sale    : {quantity} {ticker} at {sell_price: .2f} on {sell_datetime} with fee of {transaction_cost_eur}")
        else:
          raise ValueError(f"Ticker {ticker} not found in portfolio.")


    def object_print_nice(self,obj):
          for key, value in vars(obj).items():
              print_key = key

              print_key = print_key.replace('_',' ')
              print_key = print_key.title()
              print_key = print_key.replace(' Roi ',' ROI ')
              print_key = print_key.replace(' Roi',' ROI')
              print_key = print_key.replace('N Sales','Number of Sales')

              if isinstance(value, float):
                if (print_key == "Quantity"):
                  print(f"\t{print_key}: {value}")
                else:
                  match = re.match(r'.*_roi.*', key)
                  if match:
                    unit = ' %'
                  else:
                    unit = ''
                  print(f"\t{print_key}: {value: .2f}{unit}")
              else:
                print(f"\t{print_key}: {value}")
              
          print()


    def generate_report(self,verbose):
        verbose_str = str(verbose)
        print()
        print(f"--- ShareDeal, generating_report (verbose = {verbose_str}) begin ---------------\n")
        print(f"Portfolio Owner: {self.owner}")
        print(f"Portfolio Platform: {self.platform}\n")
        print(f"Portfolio Shares:")


        # Realized Summary
        rz_sum_total_invested = 0
        rz_sum_total_profit_before_tax_and_fees = 0
        rz_sum_total_fees = 0
        rz_total_tax = 0
        rz_tax_rates = []
       
        # Unrealized Summary
        ur_sum_total_currently_invested = 0
        ur_sum_total_profit_before_tax_and_fees = 0

        for ticker, v in self.shares.items():
          print(f"Share: {ticker} {v.name}")
          print(f"-----  ----")

          if v.trailingPE != '.':
            print(f"Trailing PE (Price:Earnings): {v.trailingPE}")
          if v.trailingEps != '.':
            print(f"Trailing EPS (Earnings Per Share): {v.trailingEps}")
          if v.forwardPE != '.':
            print(f"Forward PE: {v.forwardPE}")
          if v.forwardEps != '.':
            print(f"Forward EPS: {v.forwardEps}")
          if v.trailingAnnualDividendRate != '.':
            print(f"Trailing Annual Dividend Rate: {v.trailingAnnualDividendRate}")
          if v.trailingAnnualDividendYield != '.':
            print(f"Trailing Annual Dividend Yield: {v.trailingAnnualDividendYield}")

          if verbose:
            tas = v.get_transactions()
            for t in tas:
              if isinstance(t,SellTransaction):
                print('-')
              else:
                print('+')
              print(t)
            ch = v.CurrentHolding
            print('.')
            print(ch)
            print()
          print()


          print('\tRealized Summary')
          print('\t----------------')
          rzs = v.realizedSummary()
          if rzs is None:
            print('\tNo sell transactions')
            print()
          else:
            if verbose:
              print('=')
              print(rzs)
              print('=')
            self.object_print_nice(rzs)
            rz_sum_total_invested += rzs.total_sum_invested
            rz_sum_total_profit_before_tax_and_fees += rzs.total_profit_before_tax_and_fees
            rz_sum_total_fees += rzs.total_transactions_cost_eur
            rz_total_tax += rzs.total_tax
            rz_tax_rates.append(rzs.mean_tax_rate)
          
          print('\tUnrealized Summary')
          print('\t------------------')
          urs = v.getUnRealizedSummary()
          if verbose:
            print('=')
            print(urs)
            print('=')

          self.object_print_nice(urs)

          ur_sum_total_currently_invested += urs.current_invested
          ur_sum_total_profit_before_tax_and_fees += urs.unrealized_profit_before_tax

        print('Realized Summary')
        print('----------------')
        if rz_sum_total_invested == 0:
          print("No realized transactions")
          print()
        else:
          print(f"Total Invested: {rz_sum_total_invested: .2f}")
          print(f"Total Profit [before tax and fees removed]: {rz_sum_total_profit_before_tax_and_fees: .2f}")
          rz_sum_invested_with_profits = rz_sum_total_invested + rz_sum_total_profit_before_tax_and_fees
          print(f"Total Invested with Profits: {rz_sum_invested_with_profits: .2f}")
          rz_sum_total_roi_before_tax_and_fees = rz_sum_total_profit_before_tax_and_fees / rz_sum_total_invested * 100
          print(f"Total Return on Investment (ROI) [before tax and fees removed]: {rz_sum_total_roi_before_tax_and_fees: .2f} %")
          print(f"Total Fees: {rz_sum_total_fees: .2f}")
          rz_sum_total_profit_before_tax = rz_sum_total_profit_before_tax_and_fees - rz_sum_total_fees
          print(f"Total Profit [before tax, after fees removed]: {rz_sum_total_profit_before_tax: .2f}")
          rz_sum_total_roi_before_tax = rz_sum_total_profit_before_tax / rz_sum_total_invested * 100
          print(f"Total Return on Investment (ROI) [before tax, after fees removed]: {rz_sum_total_roi_before_tax: .2f} %")
          print(f"Total Tax: {rz_total_tax: .2f}")
          rz_sum_total_profit_after_tax = rz_sum_total_profit_before_tax - rz_total_tax
          
          mean_tax_rate = statistics.mean(rz_tax_rates)
          print(f"Mean Tax Rate: {mean_tax_rate: .2f} %")

          print(f"Total Profit [after tax & fees removed]: {rz_sum_total_profit_after_tax: .2f}")
          rz_sum_total_roi_after_tax = rz_sum_total_profit_after_tax / rz_sum_total_invested * 100
          print(f"Total Return on Investment (ROI) [after tax & fees removed]: {rz_sum_total_roi_after_tax: .2f} %")
          print()

        print('Unrealized Summary')
        print('-------------')
        print(f"Total Currently Invested: {ur_sum_total_currently_invested: .2f}")
        print(f"Total Profit [before tax and fees removed]: {ur_sum_total_profit_before_tax_and_fees: .2f}")
        ur_sum_invested_with_profits = ur_sum_total_currently_invested + ur_sum_total_profit_before_tax_and_fees
        print(f"Total Invested with Profits: {ur_sum_invested_with_profits: .2f}")
        ur_sum_total_roi_before_tax_and_fees = ur_sum_total_profit_before_tax_and_fees / ur_sum_total_currently_invested * 100
        print(f"Total Return on Investment (ROI) [before tax and fees removed]: {ur_sum_total_roi_before_tax_and_fees: .2f} %")

        print()
        print(f"--- ShareDeal, generating_report (verbose = {verbose_str}). Done. See yah!------")
