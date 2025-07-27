from abc import ABC, abstractmethod
from typing import Dict, List

class BookingExpertsClient(ABC):
    @abstractmethod
    async def patch_master_price_list(
        self,
        price_list_id: str,
        administration_id: str,
        simple_prices: List[Dict] = None,
        complex_prices: List[Dict] = None,) -> None:
        pass