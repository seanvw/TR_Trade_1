#!python3
from functools import cached_property
from datetime import datetime
from dataclasses import dataclass
import yfinance as yf
import statistics
import pprint
import re

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

        if stock.info['shortName']:
            self.name = stock.info['shortName']
        else:
            self.name = '.'

        # Not nice but has to be fixed later for ETFs etc
        if stock.info.get('trailingPE') is not None:
            self.trailingPE = stock.info['trailingPE']
        else: 
            self.trailingPE = "."

        if stock.info.get('trailingEps') is not None:
            self.trailingEps = stock.info['trailingEps']
        else:
            self.trailingEps = "."

        if stock.info.get('forwardPE') is not None:
            self.forwardPE = stock.info['forwardPE']
        else:
            self.forwardPE = "."

        if stock.info.get('forwardEps') is not None:
            self.forwardEps = stock.info['forwardEps']
        else:
            self.forwardEps = "."

        if stock.info.get('trailingAnnualDividendRate') is not None:
            self.trailingAnnualDividendRate = stock.info['trailingAnnualDividendRate']
        else:
            self.trailingAnnualDividendRate = "."

        if stock.info.get('trailingAnnualDividendYield') is not None:
            self.trailingAnnualDividendYield = stock.info['trailingAnnualDividendYield']
        else:
            self.trailingAnnualDividendYield = "."



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

    @property
    def get_current_price(self) -> float:
      stock = yf.Ticker(self.ticker)
      if self.current_eur_price is None:
        regularMarketPrice = stock.info['regularMarketPrice']  # Get the current price
        #print(f" DEBUG {self.ticker} price {regularMarketPrice}")
        # Now a hack because it turns out that .DE tickers are provided in EUR, duh!
        # The prototype was developed assuming USD prices were always served 
        # Need to re-work this eventually 
        # .DE is Germany
        # .MU is Munich
        # .SG is Stuttgart
        # .HAM is Hamburg
        # .DU is Dusseldorf
        # .F is Frankfurt
        # .HM is Hanover
        # .BE is Berlin
        # .PA is Paris  
        # .BR is Brussels
        # .AS is Amsterdam
        # .L is London
        # .VI is Vienna
        # .MI is Milan
        # .HE is Helsinki
        # .ST is Stockholm
        # .CO is Copenhagen
        # .OL is Oslo
        # .FI is Paris
        # .IR is Dublin
        # .VI is Vienna
        # .SW is Switzerland
        # .SG is Singapore
        # .HK is Hong Kong
        # .TO is Toronto
        # .AX is Australia
        # .NZ is New Zealand


        # etc

        # EUR matches I used so far
        match = re.match(r'.*\.(DE|MU|SG|MI|HA|BE)$', self.ticker)
        if match:
            self.current_eur_price = regularMarketPrice
            #print(f"DEBUG: Taking regularMarketPrice in EUR {self.ticker} price {regularMarketPrice} ")
        else:
            self.current_eur_price =  regularMarketPrice * self.current_usd_eur
            print(f"\t....converting currency: {self.ticker} price {self.current_eur_price: .2f} USD, {regularMarketPrice} EUR, {self.current_usd_eur} USD:EUR")
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



