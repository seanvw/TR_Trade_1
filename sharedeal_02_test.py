#!python3

from portfolio import * 
import unittest
import io
import sys

class TestPortfolio(unittest.TestCase):
    portfolio = None
    output = None

    def setUp(self):
        portfolio = Portfolio(owner='SW', platform='Trade Republic', verbose_reporting=True)
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
        self.portfolio = portfolio

        # Create a StringIO object
        string_io = io.StringIO()

        # Redirect the print output to the StringIO object
        old_stdout = sys.stdout
        sys.stdout = string_io

        # Now, print something
        print(portfolio)

        # Get the output
        self.output = string_io.getvalue()

        # Reset the stdout
        sys.stdout = old_stdout
        print("Portfolio created and output captured")

    def test_portfolio_status(self):
        
        # Test the portfolio status
        # Check if the portfolio is not None
        self.assertIsNotNone(self.portfolio, "Portfolio should not be None")
        # Check if the portfolio has shares
        self.assertTrue(len(self.portfolio.shares.items()) > 0, "Portfolio should have shares")
        # Check if the portfolio has transactions
        first_key = next(iter(self.portfolio.shares))
        self.assertTrue(len(self.portfolio.shares[first_key].transactionsLog) > 0, "Portfolio should have transactions")
        # Check if the portfolio has a valid owner
        self.assertIsInstance(self.portfolio.owner, str, "Portfolio owner should be a string")
        # Check if the portfolio has a valid platform
        self.assertIsInstance(self.portfolio.platform, str, "Portfolio platform should be a string")
        # Check if the portfolio has a valid verbose reporting flag
        self.assertIsInstance(self.portfolio.verbose_reporting, bool, "Verbose reporting should be a boolean")

    def test_portfolio_output(self):
        # Test the portfolio output
        # Check if the output is not None
        self.assertIsNotNone(self.output, "Output should not be None")
        expect_output = "Total Currently Invested:  1180.00"    
        self.assertIn(expect_output, self.output, f"Output should contain {expect_output}")
            
    def tearDown(self):
        # Clean up the portfolio after each test
        self.portfolio = None
        print("Portfolio cleaned up\n")
        return super().tearDown()
            

if __name__ == '__main__':
    unittest.main()



