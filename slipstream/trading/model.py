from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union, Callable, Tuple, NamedTuple, Set, List
import math
import pandas as pd
from abc import ABC, abstractmethod
from .pricing import *


class TradeType(Enum):
    Long = 1
    Short = 2

    @staticmethod
    def from_order_action(action: 'OrderAction') -> 'TradeType':
        return {OrderAction.Buy: TradeType.Long,
                OrderAction.BuyToCover: TradeType.Long,
                OrderAction.Sell: TradeType.Short,
                OrderAction.SellShort: TradeType.Short}[action]

    @staticmethod
    def from_position(position: int) -> 'TradeType':
        if position == 0:
            return TradeType.Flat
        return TradeType.Long if position > 0 else TradeType.Short


class Trade:
    def __init__(self, trade_type: TradeType, size: int, entry: PriceLike = None, exit: PriceLike = None, cost: PriceLike = 0.0, price_mult: float = 1.0):
        self.type = trade_type
        self.size = size
        self.entry = entry
        self.exit = exit
        self.cost = Price(cost)
        self.price_mult = price_mult if price_mult is not None else 1.0
        self.time_entered: pd.Timestamp = None
        self.time_exited: pd.Timestamp = None

    @property
    def profit(self) -> Price:
        mult = 1 if self.type == TradeType.Long else -1
        profit_in_points = mult * self.size * (self.exit - self.entry)
        return Price(profit_in_points * self.price_mult)

    def __repr__(self):
        return f"{self.profit} from {self.type} {self.size}"

    # -------------- Logging --------------
    def fields_to_log(self) -> List[str]:
        return [
            self.type.name,
            str(self.size),
            str(float(self.profit)),
            str(float(self.entry)),
            str(float(self.exit)),
            str(float(self.cost)),
            self.time_entered.isoformat(timespec='microseconds'),
            self.time_exited.isoformat(timespec='microseconds')
        ]

    @classmethod
    def field_names_to_log(cls) -> List[str]:
        return [
            "Type",
            "Size",
            "Profit",
            "Entry",
            "Exit",
            "Cost",
            "Entry Time",
            "Exit Time"
        ]


class OrderType(Enum):
    Market = 1
    Limit = 2
    StopMarket = 3
    StopLimit = 4
    TrailingStopMarket = 5
    TrailingStopLimit = 6


class OrderAction(Enum):
    Buy = 1
    Sell = 2
    SellShort = 3
    BuyToCover = 4

    def __neg__(self):
        return {self.Buy: self.Sell,
                self.Sell: self.Buy,
                self.SellShort: self.BuyToCover,
                self.BuyToCover: self.SellShort}[self]


OrderExecutionCallback = Callable[['OrderExecution'], None]


@dataclass
class Order:
    action: OrderAction
    size: int
    type: OrderType = OrderType.Market
    limit: PriceLike = None
    stop: PriceLike = None
    peak: PriceLike = None
    time_sent: pd.Timestamp = None
    on_execution: Optional[OrderExecutionCallback] = None
    activated: bool = True  # Used for Stop order types

    def is_buying(self) -> bool:
        return True if self.action in (OrderAction.Buy, OrderAction.BuyToCover) else False

    def is_stop_type(self) -> bool:
        return self.type in (
            OrderType.StopLimit,
            OrderType.StopMarket,
            OrderType.TrailingStopLimit,
            OrderType.TrailingStopMarket
        )
    
    def is_trailing_type(self) -> bool:
        return self.type in (
            OrderType.TrailingStopLimit,
            OrderType.TrailingStopMarket
        )

    # def can_be_fulfilled_with(self,
    #                           price: PriceLike = None,
    #                           prices: PriceRange = None) -> Tuple[bool, Optional['OrderExecution']]:
    #     cmp_range = PriceRange(prices=(price, price)) if price is not None else prices
    #     assert cmp_range is not None, "Must have value for price or prices"
    #     if self.type == OrderType.Market:
    #         return True, OrderExecution(order=self, size=self.size,
    #                                     price=cmp_range.high if self.action == OrderAction.Buy else cmp_range.low)
    #     elif self.type == OrderType.Limit:
    #         assert self.limit is not None, f"limit must be set for order type {self.type}"
    #         if (self.action == OrderAction.Buy and self.limit > cmp_range.low) or \
    #            (self.action != OrderAction.Buy and self.limit < cmp_range.high):
    #             return True, OrderExecution(order=self, size=self.size, price=self.limit)
    #         else:
    #             return False, None
    #     raise NotImplementedError(f"Cannot handle order type {self.type}")


class OrderExecutionResult(Enum):
    Unknown = 0
    Whole = 1
    Partial = 2
    Expired = 3


class OrderExecution:
    def __init__(self, order: Order, price: PriceLike, size: int = 0, cost: PriceLike = 0.0,
                 result: OrderExecutionResult = OrderExecutionResult.Whole):
        self.order = order
        self.price = price
        self.size = size
        self.result = result
        if self.size == 0 and self.result == OrderExecutionResult.Whole:
            self.size = self.order.size
        self.cost = Price(cost)
        self.time_received: pd.Timestamp = None
        self.time_executed: pd.Timestamp = None

    def partial_cost(self, size: int = None, ratio: float = None) -> Price:
        if size is not None:
            return self.cost * (size / self.size)
        elif ratio is not None:
            assert ratio <= 1.0, "'ratio' should be <= 1.0"
            return self.cost * ratio
        else:
            raise ValueError("Must provide 'size' or 'ratio'")

    def __repr__(self):
        act = {OrderAction.Buy: "Bought",
               OrderAction.Sell: "Sold",
               OrderAction.SellShort: "Shorted",
               OrderAction.BuyToCover: "Covered"}[self.order.action]
        return f"{act} {self.size} at {self.price}"

    @staticmethod
    def execution_from(order: Order, price: PriceLike = None, size: int = None, cost: PriceLike = 0.0) -> 'OrderExecution':
        size = size or order.size
        price = Price(price) or Price(order.limit)
        result = OrderExecutionResult.Whole if size == order.size else OrderExecutionResult.Partial
        retval = OrderExecution(
            order=order,
            price=price,
            cost=cost,
            result=result
        )




TradePlan_HoldingPeriod = Union[int, pd.Timestamp, pd.Timedelta]


class TradePlan(NamedTuple):
    """ Describes a plan to enter and exit trade.
    """
    type: TradeType
    size: int
    limit: Optional[float] = None
    target: Optional[float] = None
    stop: Optional[float] = None
    trail_stop: Optional[float] = None
    hold_period: Optional[TradePlan_HoldingPeriod] = None


@dataclass
class BookState:
    bid: PriceLike
    ask: PriceLike
    last: PriceLike
    last_vol: Optional[int] = None


class BookStateObserver(ABC):
    @abstractmethod
    def observe_book_state(self, book_state: BookState) -> None:
        raise NotImplementedError


class BookStatePublisher(ABC):
    @abstractmethod
    def subscribe(self, observer: BookStateObserver):
        raise NotImplementedError


class Trader(ABC):
    @abstractmethod
    def add_trade_plan(self, plan: TradePlan):
        raise NotImplementedError
