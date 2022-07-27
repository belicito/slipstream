
from .model import *
from enum import IntEnum
from typing import Tuple, List


class SimTrade(Trade):
    def __init__(self, is_open):
        ...


class PositionTracker:
    def __init__(self, initial_equity: float = 10000.0, buy_cost: float = 0, sell_cost: float = 0):
        self.buy_cost = buy_cost
        self.sell_cost = sell_cost
        self._equity_value = initial_equity
        self._trades: List[SimTrade] = []
        self._position: int = 0
        self._avg_price: float = math.nan

    def add_execution(self, execution: OrderExecution):
        if self.current_trade is None:
            self._position = execution.size * self._position_sign_from(order_action=execution.order.action)
            trade = SimTrade(trade_type=TradeType.from_position(self._position),
                             size=execution.size,
                             entry_price=execution.price)
            self._trades.append(trade)
        else:
            new_trade = self.current_trade.add_execution(execution)
            if new_trade:
                self._trades.append(new_trade)

    def update_book_state(self, book_state: BookState):
        raise NotImplementedError

    @property
    def equity_value(self) -> float:
        # TODO: if market price is set, return mark-to-market value
        return self._equity_value

    @property
    def trades(self) -> List[SimTrade]:
        return self._trades

    @property
    def current_trade(self) -> Optional[SimTrade]:
        if len(self._trades) > 0 or self._trades[-1].is_open:
            return self._trades[-1]
        return None

    @property
    def position(self) -> int:
        return self._position

    @staticmethod
    def _position_sign_from(order_action: OrderAction = None, trade_type: TradeType = None) -> int:
        if order_action is not None:
            return 1 if order_action == OrderAction.Buy else -1
        if trade_type is not None:
            return 1 if trade_type == TradeType.Long else -1
        raise ValueError(f"Unable to use given value(s)")

    def _close_current_trade(self, price: float):
        if self._position != 0 and len(self._trades) > 0:
            trade = self._trades[-1]
            profit = (price - trade.entry_price) * self._position
            self._equity_value += profit
            self._position = 0
        else:
            print(f"WARN: Trying to close trade but there is no position")
