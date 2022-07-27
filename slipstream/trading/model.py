from enum import Enum
from typing import Optional, Union, Callable, Tuple, NamedTuple
import math
import pandas as pd
from abc import ABC, abstractmethod
from .pricing import *


class TradeType(Enum):
    Unspecified = 0
    Long = 1
    Short = 2
    Flat = 3

    @staticmethod
    def from_order_action(action: 'OrderAction') -> 'TradeType':
        return TradeType.Long if action == OrderAction.Buy else TradeType.Short

    @staticmethod
    def from_position(position: int) -> 'TradeType':
        if position == 0:
            return TradeType.Flat
        return TradeType.Long if position > 0 else TradeType.Short


class Trade:
    def __init__(self, trade_type: TradeType, size: int, entry_price: float):
        self.type = trade_type
        self.size = size
        self.entry_price = entry_price
        self.mtm_profit: float = 0
        self.run_up: float = 0
        self.draw_down: float = 0

    def assess(self, price_range: PriceRange):
        assert not math.isnan(self.entry_price)
        if self.type == TradeType.Long:
            self.mtm_profit = price_range.hl2 - self.entry_price
        else:
            self.mtm_profit = self.entry_price - price_range.hl2
        self.run_up = max(self.run_up, self.mtm_profit)
        self.draw_down = min(self.draw_down, self.mtm_profit)

    def add_execution(self, execution: 'OrderExecution') -> Optional['Trade']:
        exec_trade_type = TradeType.from_order_action(execution.order.action)
        if exec_trade_type == self.type:
            trade_cost = self.size * self.entry_price
            trade_cost += execution.size * execution.price
            self.size += execution.size
            self.entry_price = trade_cost / self.size
            return None
        else:
            raise NotImplementedError


class OrderType(Enum):
    Unspecified = 0
    Market = 1
    Limit = 2


class OrderAction(Enum):
    Unspecified = 0
    Buy = 1
    Sell = 2
    SellShort = 3


class Order(NamedTuple):
    action: OrderAction
    size: int
    type: OrderType = OrderType.Market
    limit: float = None
    on_execution: Optional[Callable[['OrderExecution'], None]] = None

    def can_be_fulfilled_with(self,
                              price: PriceLike = None,
                              prices: PriceRange = None) -> Tuple[bool, Optional['OrderExecution']]:
        cmp_range = PriceRange(prices=(price, price)) if price is not None else prices
        assert cmp_range is not None, "Must have value for price or prices"
        if self.type == OrderType.Market:
            return True, OrderExecution(order=self, size=self.size,
                                        price=cmp_range.high if self.action == OrderAction.Buy else cmp_range.low)
        elif self.type == OrderType.Limit:
            assert self.limit is not None, f"limit must be set for order type {self.type}"
            if (self.action == OrderAction.Buy and self.limit > cmp_range.low) or \
               (self.action != OrderAction.Buy and self.limit < cmp_range.high):
                return True, OrderExecution(order=self, size=self.size, price=self.limit)
            else:
                return False, None
        raise NotImplementedError(f"Cannot handle order type {self.type}")


class OrderExecutionResult(Enum):
    Unknown = 0
    Whole = 1
    Partial = 2
    Expired = 3


class OrderExecution:
    def __init__(self, order: Order, price: float, size: int = 0,
                 result: OrderExecutionResult = OrderExecutionResult.Whole, is_real: bool = False):
        self.order = order
        self.price = price
        self.size = size
        self.result = result
        if self.size == 0 and self.result == OrderExecutionResult.Whole:
            self.size = self.order.size
        self.is_real = is_real


TradePlan_HoldingPeriod = Union[int, pd.Timestamp, pd.Timedelta]


class TradePlan(NamedTuple):
    """ Describes a plan to enter and exit trade.
    """
    type: TradeType = TradeType.Unspecified
    size: int = 0
    limit: Optional[float] = None
    target: Optional[float] = None
    stop: Optional[float] = None
    trail_stop: Optional[float] = None
    hold_period: Optional[TradePlan_HoldingPeriod] = None


class BookState(ABC):
    @property
    @abstractmethod
    def repr_price(self) -> float:
        raise NotImplementedError


class BookStateObserver(ABC):
    @abstractmethod
    def receive(self, book_state: BookState):
        raise NotImplementedError


class BookStatePublisher(ABC):
    @abstractmethod
    def subscribe(self, observer: BookStateObserver):
        raise NotImplementedError


class Trader(ABC):
    @abstractmethod
    def add_trade_plan(self, plan: TradePlan):
        raise NotImplementedError
