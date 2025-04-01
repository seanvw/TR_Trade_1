#!python3

from portfolio import * 
import unittest

class TestPortfolio(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio(owner='SW', platform='Trade Republic', verbose_reporting=True)
        self.year = 2023
        self.month = 10
        self.tc_eur = 1.00

    def test_add(self):
        
        self.assertEqual(self.portfolio.add_share(ticker='AAPL', 
                                             buy_price=160, 
                                             quantity=1.5, 
                                             buy_datetime=datetime(self.year, self.month, 1, 9, 30), 
                                             transaction_cost_eur=self.tc_eur), None)
        
    def test_add_invalid_transaction_cost(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=160, 
                                quantity=-1.5, 
                                buy_datetime=datetime(self.year, self.month, 1, 9, 31), 
                                transaction_cost_eur=-1.00)
    
    def test_add_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=160, 
                                quantity=-1.5, 
                                buy_datetime=datetime(self.year, self.month, 1, 9, 32), 
                                transaction_cost_eur=self.tc_eur)
    def test_add_invalid_buy_price(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=-160, 
                                quantity=1.5, 
                                buy_datetime=datetime(self.year, self.month, 1, 9, 33), 
                                transaction_cost_eur=self.tc_eur)
            
    def test_add_invalid_buy_datetime(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=160, 
                                quantity=1.5, 
                                buy_datetime=datetime(self.year+1000, self.month, 1, 9, 34), 
                                transaction_cost_eur=self.tc_eur)
            
    def test_add_invalid_zero_quantity(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=160, 
                                quantity=0, 
                                buy_datetime=datetime(self.year, self.month, 1, 9, 35), 
                                transaction_cost_eur=self.tc_eur)
    def test_add_invalid_zero_buy_price(self):
        with self.assertRaises(ValueError):
            self.portfolio.add_share(ticker='AAPL', 
                                buy_price=0, 
                                quantity=1.5, 
                                buy_datetime=datetime(self.year, self.month, 1, 9, 36), 
                                transaction_cost_eur=self.tc_eur)
            
    def tearDown(self):
        # Clean up the portfolio after each test
        self.portfolio = None
        return super().tearDown()
            
        

if __name__ == '__main__':
    unittest.main()



