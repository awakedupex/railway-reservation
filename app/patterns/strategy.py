from abc import ABC, abstractmethod


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, base_price: float) -> float:
        pass


class StandardPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price


class StudentDiscountPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price * 0.85


class SeniorCitizenPricing(PricingStrategy):
    def calculate(self, base_price: float) -> float:
        return base_price * 0.75


class PricingContext:
    def __init__(self, strategy: PricingStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: PricingStrategy):
        self._strategy = strategy

    def get_price(self, base_price: float) -> float:
        return self._strategy.calculate(base_price)
