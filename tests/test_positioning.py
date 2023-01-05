# import unittest
import pytest
from slipstream.trading import TradeType, OrderAction, Order, OrderExecution, Price
from slipstream.trading.positions import PositionTracker, Position

    
# class TestPositioning(unittest.TestCase):

    # def setUp(self) -> None:
    #     self.p = PositionTracker(initial_equity=10000.0)

# p = PositionTracker(initial_equity=10000.0)

@pytest.fixture()
def p():
    return PositionTracker(initial_equity=10000.0)

def start_with(p: PositionTracker, equity: float, position: int = 0, entry_price: float = 0.0):
    if position > 0:
        bought(p, size=abs(position), price=entry_price)
    elif position < 0:
        sold_short(p, size=abs(position), price=entry_price)

def bought(p: PositionTracker, size: int, price: float):
    _executed(p, action=OrderAction.Buy, size=size, price=price)
    print(f"Bought {size} at {price}")

def sold(p: PositionTracker, size: int, price: float):
    _executed(p, action=OrderAction.Sell, size=size, price=price)
    print(f"Sold {size} at {price}")

def sold_short(p, size: int, price: float):
    _executed(action=OrderAction.SellShort, size=size, price=price)
    print(f"Sold-short {size} at {price}")

def bought_to_cover(p, size: int, price: float):
    _executed(action=OrderAction.BuyToCover, size=size, price=price)
    print(f"Cover-bought {size} at {price}")

def _executed(p: PositionTracker, action: OrderAction, size: int, price: float):
    order = Order(action=action, size=size)
    execution = OrderExecution(order=order, size=order.size, price=price, cost=1.0)
    p.add_execution(execution)

def position_status(p: PositionTracker) -> str:
    pos_desc = str(p.position) if p.position else "Flat"
    return f"{pos_desc} w/ {len(p.trades)} trades"

def test_single_long_profitable(p):
    _test_single_profitable_trade(TradeType.Long)

def test_single_short_profitable(p):
    _test_single_profitable_trade(TradeType.Short, unit_size=200)

def test_2x_long_profit(p):
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
    assert len(p.trades) == 2
    assert p.equity_value == 10300.0

def test_composite_long_profit(p):
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.Buy, size=100),
        price=10.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.Buy, size=100),
        price=11.0
    ))
    assert p.position.entry == 10.5

    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.Sell, size=200),
        price=12.0
    ))
    assert len(p.trades) == 1
    assert p.equity_value == 10300.0

def test_composite_short_profit(p):
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.SellShort, size=100),
        price=10.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.SellShort, size=100),
        price=11.0
    ))
    assert p.position.entry == 10.5

    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.BuyToCover, size=200),
        price=9.0
    ))
    assert len(p.trades) == 1
    assert p.equity_value == 10300.0

def test_composite_short_loss(p):
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.SellShort, size=100),
        price=10.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.SellShort, size=100),
        price=11.0
    ))
    assert p.position.entry == 10.5

    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.BuyToCover, size=200),
        price=11.5
    ))
    assert len(p.trades) == 1
    assert p.equity_value == 9800.0

def test_multi_trades_closed(p, opening_size=200):
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.SellShort, size=opening_size),
        price=10.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.BuyToCover, size=100),
        price=11.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=OrderAction.BuyToCover, size=100),
        price=11.5
    ))
    assert len(p.trades) == 2
    assert p.equity_value == 9750.0

def test_multi_trades_opening(p):
    test_multi_trades_closed(p, opening_size=300)
    assert p.position.size == 100

def test_multi_in_multi_out_closed(p):
    start_with(p, equity=10000.0, position=100, entry_price=10.0)
    bought(p, size=200, price=11.0)
    sold(p, size=100, price=12.0)
    sold(p, size=200, price=11.0)
    assert p.position == None
    assert len(p.trades) == 2
    assert p.equity_value == 10200.0 - 4.0

def test_multi_in_multi_out_open(p):
    p = p
    start_with(p, equity=10000.0, position=100, entry_price=10.0)
    print(position_status(p))
    bought(p, size=200, price=11.0)
    print(position_status(p))
    sold(p, size=100, price=12.0)
    print(position_status(p))
    bought(p, size=200, price=11.0)
    print(position_status(p))
    sold(p, size=100, price=11.0)
    print(position_status(p))
    sold(p, size=100, price=12.0)
    print(position_status(p))
    assert p.position.size == 200
    assert len(p.trades) == 3

def _test_single_profitable_trade(trade_type: TradeType, unit_size: int = 100):
    assert trade_type in (TradeType.Long, TradeType.Short)
    ord_act = OrderAction.Buy if trade_type == TradeType.Long else OrderAction.SellShort
    base_price = Price(10.0)
    price_diff = Price(1.0)
    price_diff_mult = 1 if trade_type == TradeType.Long else -1
    better_price = base_price + (price_diff_mult * price_diff)
    p = PositionTracker(initial_equity=10000.0)

    p.add_execution(OrderExecution(
        order=Order(action=ord_act, size=unit_size),
        price=base_price,
        cost=1.0
    ))
    p.add_execution(OrderExecution(
        order=Order(action=-ord_act, size=unit_size),
        price=better_price,
        cost=1.0
    ))
    assert len(p.trades) == 1
    assert p.equity_value == 10000.0 + (unit_size * price_diff) - 2.0


# if __name__ == '__main__':
#     unittest.main()
