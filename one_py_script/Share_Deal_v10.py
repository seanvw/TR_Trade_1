from sys import version
from functools import cached_property
import yfinance as yf
from datetime import datetime
from dataclasses import dataclass
import statistics
import re

# changed to data classes

@dataclass
class Transaction():
    quantity: float
    datetime: datetime
    transaction_cost_eur: float

    def __post_init__(self):
        pass

@dataclass
class BuyTransaction(Transaction):
    buy_price: float

    def __post_init__(self):
        super().__post_init__()

    @property
    def invested(self):
        return (self.buy_price * self.quantity) + self.transaction_cost_eur

@dataclass
class SellTransaction(Transaction):
    buy_price: float
    sell_price: float
    tax: float

    def __post_init__(self):
        super().__post_init__()

    @cached_property
    def profit_before_tax(self) -> float:
        return (self.sell_price - self.buy_price) * self.quantity

    @cached_property
    def profit_after_tax(self) -> float:
        return (self.profit_before_tax - self.tax)

    @cached_property
    def tax_rate(self) -> float:
        return self.tax / self.profit_before_tax

    @cached_property
    def roi_after_tax(self) -> float:
        return self.profit_after_tax / (self.buy_price * self.quantity) * 100

    @cached_property
    def roi_before_tax_and_fees(self) -> float:
        return self.profit_before_tax / (self.buy_price * self.quantity) * 100

    @cached_property
    def sum_invested(self) -> float:
        return (self.buy_price * self.quantity)


@dataclass
class CurrentHolding():
    buy_price: float
    quantity: float
    last_transaction_datetime: datetime
    total_transactions_cost_eur: float

    def __post_init__(self):
        pass

    @property
    def current_invested(self):
        return self.buy_price * self.quantity

    def __str__(self):
      current_invested = self.current_invested
      print(f"CurrentHolding(buy_price={self.buy_price}, quantity={self.quantity}, \
current_invested={current_invested}, total_transactions_cost_eur={self.total_transactions_cost_eur}, \
last_transaction_datetime={self.last_transaction_datetime}")
      return "."

@dataclass
class ExchangeRate_current_usd_eur():

  def __post_init__(self):
        stock = yf.Ticker("USDEUR=X")
        self.current_usd_eur = stock.info['regularMarketPrice']

  def get_current_usd_eur(self):
    return self.current_usd_eur

@dataclass
class RealizedSummary():
    ticker: str
    n_sales: int
    total_profit_before_tax_and_fees: float
    total_tax: float
    total_profit_after_tax_with_fees:float
    total_transactions_cost_eur: float
    total_profit_after_tax_and_fees: float
    mean_roi_before_tax_and_fees: float
    mean_roi_after_tax: float
    total_sum_invested: float


    def __post_init__(self):
       pass

@dataclass
class UnRealizedSummary():
    ticker: str
    buy_price: float
    quantity: float
    last_transaction_datetime: datetime
    current_eur_price: float
    current_value: float
    current_roi: float
    current_usd_eur: float
    current_invested: float
    unrealized_profit_before_tax: float

@dataclass
class Share():
    ticker: str
    current_usd_eur: float
    transactionsLog: list = None
    CurrentHolding: CurrentHolding = None
    current_eur_price: float = None

    def __post_init__(self):
        stock = yf.Ticker(self.ticker)
        self.name = stock.info['shortName']
        self.trailingPE = stock.info['trailingPE']
        self.trailingEps = stock.info['trailingEps']
        self.forwardPE = stock.info['forwardPE']
        self.forwardEps = stock.info['forwardEps']
        self.trailingAnnualDividendRate = stock.info['trailingAnnualDividendRate']
        self.trailingAnnualDividendYield = stock.info['trailingAnnualDividendYield']

    def add_transaction(self, buy_price, quantity, buy_datetime, transaction_cost_eur):

        buy_t = BuyTransaction(buy_price=buy_price, quantity=quantity, datetime=buy_datetime, transaction_cost_eur=transaction_cost_eur)

        if self.transactionsLog is None:
          self.transactionsLog = []
        self.transactionsLog.append(buy_t)

        if self.CurrentHolding is None:
          self.CurrentHolding = CurrentHolding(buy_price=buy_t.buy_price, quantity=buy_t.quantity, last_transaction_datetime=buy_t.datetime, total_transactions_cost_eur=transaction_cost_eur)
        else:
          self.CurrentHolding.buy_price = (self.CurrentHolding.buy_price * self.CurrentHolding.quantity
            + buy_t.buy_price * buy_t.quantity) / (self.CurrentHolding.quantity + buy_t.quantity)
          self.CurrentHolding.quantity += buy_t.quantity
          self.CurrentHolding.last_transaction_datetime = buy_t.datetime
          self.CurrentHolding.total_transactions_cost_eur += transaction_cost_eur

    def sell_transaction(self, sell_price, quantity, tax, sell_datetime, transaction_cost_eur):

        sell_t = SellTransaction(buy_price=self.CurrentHolding.buy_price,
                                 sell_price=sell_price, quantity=quantity,
                                 tax=tax, datetime=sell_datetime, transaction_cost_eur=transaction_cost_eur)

        if self.transactionsLog is None:
          self.transactionsLog = []

        # update the current holding
        self.CurrentHolding.quantity -= sell_t.quantity
        self.CurrentHolding.last_transaction_datetime = sell_t.datetime
        self.CurrentHolding.total_transactions_cost_eur += transaction_cost_eur
        self.transactionsLog.append(sell_t)

    def realizedSummary(self):

      total_profit_before_tax_and_fees = 0
      total_profit_after_tax_with_fees = 0
      total_transactions_cost_eur = 0
      n_sales = 0
      total_tax = 0
      roi_before_tax_and_fees = []
      roi_after_tax = []
      total_sum_invested = 0
      for transaction in self.transactionsLog:
        if isinstance(transaction,SellTransaction):
          total_profit_before_tax_and_fees += transaction.profit_before_tax
          total_profit_after_tax_with_fees += transaction.profit_after_tax
          total_transactions_cost_eur += transaction.transaction_cost_eur
          total_sum_invested += transaction.sum_invested
          n_sales += 1
          total_tax += transaction.tax
          roi_before_tax_and_fees.append(transaction.roi_before_tax_and_fees)
          roi_after_tax.append(transaction.roi_after_tax)
        elif isinstance(transaction,BuyTransaction):
          total_transactions_cost_eur += transaction.transaction_cost_eur
        else:
          raise ValueError(f"Unknown transaction type: {type(transaction)}")

      # means
      mean_roi_before_tax_and_fees = 0
      mean_roi_after_tax = 0
      if n_sales > 0:
        mean_roi_before_tax_and_fees = statistics.mean(roi_before_tax_and_fees)
        mean_roi_after_tax = statistics.mean(roi_after_tax)

        # another profit calc
        total_profit_after_tax_and_fees = total_profit_after_tax_with_fees - total_transactions_cost_eur



        return RealizedSummary(ticker=self.ticker,
                               n_sales=n_sales,
                               total_profit_before_tax_and_fees=total_profit_before_tax_and_fees,
                               total_tax=total_tax,
                               total_profit_after_tax_with_fees=total_profit_after_tax_with_fees,
                               total_transactions_cost_eur=total_transactions_cost_eur,
                               total_profit_after_tax_and_fees=total_profit_after_tax_and_fees,
                               mean_roi_before_tax_and_fees=mean_roi_before_tax_and_fees,
                               mean_roi_after_tax=mean_roi_after_tax,
                               total_sum_invested=total_sum_invested
                               )
      else:
        return None

    @cached_property
    def get_current_price(self) -> float:
      stock = yf.Ticker(self.ticker)
      if self.current_eur_price is None:
        price_usd = stock.info['regularMarketPrice']  # Get the current price
        self.current_eur_price = price_usd * self.current_usd_eur
      return self.current_eur_price

    @property
    def get_current_value(self) -> float:
      return self.get_current_price * self.CurrentHolding.quantity

    @property
    def get_current_roi(self) -> float:
      cp = self.get_current_price
      return (cp - self.CurrentHolding.buy_price) / self.CurrentHolding.buy_price * 100

    def get_transactions(self) -> list:
      return self.transactionsLog

    def getUnRealizedSummary(self) -> UnRealizedSummary:
      return UnRealizedSummary(ticker=self.ticker,
                               buy_price=self.CurrentHolding.buy_price,
                               quantity=self.CurrentHolding.quantity,
                               last_transaction_datetime=self.CurrentHolding.last_transaction_datetime,
                               current_eur_price=self.get_current_price,
                               current_value=self.get_current_value,
                               current_roi=self.get_current_roi,
                               current_usd_eur=self.current_usd_eur,
                               current_invested=self.CurrentHolding.current_invested,
                               unrealized_profit_before_tax=self.get_current_value - self.CurrentHolding.current_invested
                               )


@dataclass
class Portfolio():
    owner: str
    platform: str

    def __post_init__(self):
        self.shares = {}

    def __str__(self) -> str:
      self.generate_report(verbose=True)
      self.generate_report(verbose=False)
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
        print(f"Buying {quantity} {ticker} at {buy_price}")
        share.add_transaction(buy_price, quantity, buy_datetime, transaction_cost_eur)


    def sell_share(self, ticker, sell_price, quantity, tax, sell_datetime, transaction_cost_eur):
        if ticker in self.shares:
          share = self.shares[ticker]
          #print(f"sell_share, Ticker {ticker} found in portfolio.")
          share.sell_transaction(sell_price, quantity, tax, sell_datetime, transaction_cost_eur)
          print(f"Sold {quantity} {ticker} at {sell_price}, paid tax of {tax}")
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
        print(f"------------------  generate_report (verbose = {verbose_str}) begin ---------------\n")
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

        print(f"------------------  generate_report (verbose = {verbose_str}) done  ----------------\n")




portfolio = Portfolio(owner='SW', platform='Trade Republic')
# Current transaction cost for a sale or buy
tc_eur = 1.00

portfolio.add_share(ticker='AAPL', buy_price=160, quantity=1.5, buy_datetime=datetime(2023, 10, 1, 9, 30), transaction_cost_eur=tc_eur)
#print(portfolio)

portfolio.add_share(ticker='AAPL', buy_price=200, quantity=1.5, buy_datetime=datetime(2023, 10, 2, 10, 30), transaction_cost_eur=tc_eur)


portfolio.sell_share(ticker='AAPL', sell_price=240, quantity=1.0, tax=15, sell_datetime=datetime(2023, 11, 1, 14, 30), transaction_cost_eur=tc_eur)


portfolio.sell_share(ticker='AAPL', sell_price=240, quantity=1.0, tax=15, sell_datetime=datetime(2023, 11, 2, 18, 30), transaction_cost_eur=tc_eur)


#print(portfolio)

#print(portfolio)

portfolio.add_share(ticker='GOOG', buy_price=100.0, quantity=10, buy_datetime=datetime(2023, 12, 2, 10, 30), transaction_cost_eur=tc_eur)
print(portfolio)
