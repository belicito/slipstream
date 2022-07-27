from .model import *
from .pricing import *
from typing import List, Dict, Union, Any, Optional
from abc import ABC


class Report:
    ...


class Simulation(ABC):
    """ This class orchestrates modules needed in a simulation exercise:

    - market data,
    - model prediction,
    - trader,
    - position tracking,
    - final report, etc.
    """
    def __init__(self, market_data: Union[str], model: Union[str], trader: Union[str] = None):
        self.market_data = market_data
        self.model = model
        self.trader = self._get_trader(trader)

    def launch(self):
        ...

    @property
    def report(self) -> Report:
        ...

    def _get_trader(self, trader: Any) -> Trader:
        ...
