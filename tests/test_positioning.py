import unittest
from slipstream.trading import OrderAction, Order, OrderExecution
from slipstream.trading.positions import PositionTracker


class MyTestCase(unittest.TestCase):

    def test_single_long_profit(self):
        p = PositionTracker(initial_equity=10000.0)
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Buy, size=100),
            price=10.0
        ))
        self.assertEqual(len(p.trades), 1)
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Sell, size=100),
            price=11.0
        ))
        self.assertEqual(len(p.trades), 1)
        self.assertEqual(p.equity_value, 10100.0)

    def test_2x_long_profit(self):
        p = PositionTracker(initial_equity=10000.0)
        trade1_size = 100
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Buy, size=trade1_size),
            price=10.0
        ))
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Sell, size=trade1_size),
            price=11.0
        ))
        trade2_size = 200
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Buy, size=trade2_size),
            price=10.5
        ))
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Sell, size=trade2_size),
            price=11.5
        ))
        self.assertEqual(len(p.trades), 2)
        self.assertEqual(p.equity_value, 10300.0)

    def test_composite_long_profit(self):
        p = PositionTracker(initial_equity=10000.0)
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Buy, size=100),
            price=10.0
        ))
        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Buy, size=100),
            price=11.0
        ))
        self.assertEqual(p.current_trade.entry_price, 10.5)

        p.add_execution(OrderExecution(
            order=Order(action=OrderAction.Sell, size=200),
            price=12.0
        ))
        self.assertEqual(len(p.trades), 1)
        self.assertEqual(p.equity_value, 10300.0)


if __name__ == '__main__':
    unittest.main()
