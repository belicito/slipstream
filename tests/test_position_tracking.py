# import unittest
import pytest
import pandas as pd
from slipstream.trading import TradeType, OrderAction, Order, OrderType, OrderExecution, Price, PriceLike
from slipstream.trading.positions import PositionTracker2 as PositionTracker

    
class PositionTrackerUnderTest(PositionTracker):
    def __init__(self, initial_equity: float = 10000, buy_cost: float = 0, sell_cost: float = 0):
        super().__init__(initial_equity, buy_cost, sell_cost)
        self.timestamp = pd.Timestamp.now()

    def bought(self, size: int, price: PriceLike, order_type: OrderType = OrderType.Market, cost: PriceLike = 0.0):
        order = Order(OrderAction.Buy, size=size, type=order_type)
        self._make_executed(order=order, price=price, size=size, cost=cost)

    def covered(self, size: int, price: PriceLike, order_type: OrderType = OrderType.Market, cost: PriceLike = 0.0):
        order = Order(OrderAction.BuyToCover, size=size, type=order_type)
        self._make_executed(order=order, price=price, size=size, cost=cost)

    def sold(self, size: int, price: PriceLike, order_type: OrderType = OrderType.Market, cost: PriceLike = 0.0):
        order = Order(OrderAction.Sell, size=size, type=order_type)
        self._make_executed(order=order, price=price, size=size, cost=cost)

    def shorted(self, size: int, price: PriceLike, order_type: OrderType = OrderType.Market, cost: PriceLike = 0.0):
        order = Order(OrderAction.SellShort, size=size, type=order_type)
        self._make_executed(order=order, price=price, size=size, cost=cost)

    def _make_executed(self, order, price, size, cost):
        execution = OrderExecution(order=order, price=price, size=size, cost=cost)
        execution.time_received = self.timestamp - pd.Timedelta("0.000001s")
        execution.time_executed = self.timestamp
        self.add_execution(execution)
    
    def after(self, delta_desc: str):
        self.timestamp += pd.Timedelta(delta_desc)


@pytest.fixture()
def pos_tracker(request):
    t = PositionTrackerUnderTest(initial_equity=10000.0)
    path = f"x/{request.node.name}.trades.csv"
    t.start_recording_trades(path=path)
    yield t
    t.stop_recording_trades()


def test_single_long_profitable(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.bought(size=100, price=10.0, cost=1.0)
    pt.after("60s")
    pt.sold(size=100, price=11.0, cost=1.0)
    assert len(pt.trades) == 1
    assert pt.equity_value == 10098.0


def test_single_short_profitable(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.shorted(size=100, price=11.0, cost=1.0)
    pt.after("120s")
    pt.covered(size=100, price=10.0, cost=1.0)
    assert len(pt.trades) == 1
    assert pt.equity_value == 10098.0


def test_cost_negates_profit(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.shorted(size=1, price=4005.0, cost=3.0)
    pt.after("300s")
    pt.covered(size=1, price=4000.0, cost=3.0)
    assert len(pt.trades) == 1
    assert pt.equity_value == 9999.0
    

def test_2x_trades_long(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.bought(size=100, price=10.0, cost=1.0)
    pt.after("90s")
    pt.bought(size=100, price=10.0, cost=1.0)
    pt.after("300s")
    pt.sold(size=100, price=11.0, cost=1.0)
    pt.after("60s")
    pt.sold(size=100, price=12.0, cost=1.0)
    assert len(pt.trades) == 2
    assert pt.equity_value == 10296.0


def test_flip_flop_trade(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.bought(size=100, price=10.0)
    pt.after("60s")
    pt.sold(size=200, price=11.0)
    pt.after("60s")
    pt.bought(size=200, price=10.0)
    assert len(pt.trades) == 2
    assert pt.trades[0].type == TradeType.Long
    assert pt.trades[1].type == TradeType.Short
    assert pt.equity_value == 10200.0
    assert pt.position.trade_type == TradeType.Long
    assert pt.position.size == 100

def test_partial_entry_cost(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.shorted(size=200, price=101.0, cost=2.0)
    pt.after("300s")
    pt.covered(size=100, price=100.0, cost=1.0)
    assert len(pt.trades) == 1
    
    # Cost should be 1.00(half of short cost) + 1.00(covering)
    assert pt.trades[0].cost == 2.0
    
    # Since short trade already executed, full trade cost $2 already paid
    assert pt.equity_value == 10097.0

def test_partial_exit_cost(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.shorted(size=100, price=101.0, cost=1.0)
    pt.after("300s")
    pt.covered(size=300, price=100.0, cost=3.0)
    assert len(pt.trades) == 1
    
    # Cost should be 1.00(short) + 1.00(1/3 of cover cost)
    assert pt.trades[0].cost == 2.0
    
    # Since cover trade already executed, full trade cost $3 already paid
    assert pt.equity_value == 10096.0

def test_BSS_flat(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.bought(size=200, price=10.0, cost=2.0)
    pt.after("1h30m")
    pt.sold(size=100, price=10.5, cost=1.0)
    assert len(pt.trades) == 1
    assert pt.position.size == 100
    
    pt.after("5m")
    pt.sold(size=100, price=10.4, cost=1.0)
    assert len(pt.trades) == 2
    assert pt.position is None

def test_market_high_low_tracking(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.bought(size=100, price=10.0, cost=1.0)
    pt.eval_market_prices(10.1, 10.05, 9.98, 9.97, 9.90, 9.91, 9.85, 9.8, 9.9, 9.99)
    pt.after("90m")
    pt.eval_market_prices(10.1, 10.11, 10.35, 10.43, 10.55, 10.80, 11.0)
    pt.sold(size=100, price=10.5, cost=1.0)
    assert len(pt.trades) == 1
    t = pt.trades[0]
    assert t.run_up == pytest.approx(100.0, 0.0001)
    assert t.draw_down == pytest.approx(-20.0, 0.0001)

def test_market_high_low_tracking_no_drawdown(pos_tracker):
    pt: PositionTrackerUnderTest = pos_tracker
    pt.timestamp = pd.Timestamp.fromisoformat("2022-11-29T10:00:56.502619")
    pt.shorted(size=100, price=10.0, cost=1.0)
    pt.eval_market_prices(9.98, 9.97, 9.90, 9.91, 9.85, 9.8, 9.9, 9.99)
    pt.after("90m")
    pt.covered(size=100, price=9.9, cost=1.0)
    assert len(pt.trades) == 1
    t = pt.trades[0]
    assert t.run_up == pytest.approx(20.0, 0.0001)
    assert t.draw_down == pytest.approx(0.0, 0.0001)
