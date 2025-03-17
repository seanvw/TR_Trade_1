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

        # super summary
        sup_sum_total_invested = 0
        sup_sum_total_profit_before_tax_and_fees = 0
        sup_sum_total_fees = 0

        for ticker, v in self.shares.items():
          print(f"Share: {ticker} {v.name}")
          print(f"-----  ----")

          print(f"Trailing PE (Price:Earnings): {v.trailingPE}")
          print(f"Trailing EPS (Earnings Per Share): {v.trailingEps}")
          print(f"Forward PE: {v.forwardPE}")
          print(f"Forward EPS: {v.forwardEps}")
          print(f"Trailing Annual Dividend Rate: {v.trailingAnnualDividendRate}")
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
            sup_sum_total_invested += rzs.total_sum_invested
            sup_sum_total_profit_before_tax_and_fees += rzs.total_profit_before_tax_and_fees
            sup_sum_total_fees += rzs.total_transactions_cost_eur

          print('\tUnrealized Summary')
          print('\t------------------')
          urs = v.getUnRealizedSummary()
          if verbose:
            print('=')
            print(urs)
            print('=')

          self.object_print_nice(urs)

          sup_sum_total_invested += urs.current_invested
          sup_sum_total_profit_before_tax_and_fees += urs.unrealized_profit_before_tax

        print('Super Summary')
        print('-------------')
        print(f"Total Invested: {sup_sum_total_invested: .2f}")
        print(f"Total Profit [before tax and fees]: {sup_sum_total_profit_before_tax_and_fees: .2f}")

        sup_sum_total_roi_before_tax_and_fees = sup_sum_total_profit_before_tax_and_fees / sup_sum_total_invested * 100
        print(f"Total Return on Investment (ROI) [before tax and fees]: {sup_sum_total_roi_before_tax_and_fees: .2f} %")

        print(f"Total Fees: {sup_sum_total_fees: .2f}")
        sup_sum_total_profit_before_tax = sup_sum_total_profit_before_tax_and_fees - sup_sum_total_fees

        print(f"Total Profit [before tax]: {sup_sum_total_profit_before_tax: .2f}")

        sup_sum_total_roi_before_tax = sup_sum_total_profit_before_tax / sup_sum_total_invested * 100
        print(f"Total Return on Investment (ROI) [before tax]: {sup_sum_total_roi_before_tax: .2f} %")

        print()
        print(f"--- ShareDeal, generating_report (verbose = {verbose_str}). Done. See yah!------")
