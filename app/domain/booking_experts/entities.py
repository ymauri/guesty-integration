from uuid import uuid4

class SimplePrice:
    temp_id: str
    def __init__(self, date: str, value: float, currency: str):
        self.date = date
        self.currency = currency
        self.value = value
        self.temp_id = uuid4().hex

    def to_dict(self):
        return {
            "temp_id": self.temp_id,
            "date": self.date,
            "currency": self.currency,
            "value": str(self.value)
        }
        
class ComplexPrice:
    temp_id: str
    def __init__(self, arrival_date: str, value: float, currency: str, length_of_stay: int = 1):
        self.arrival_date = arrival_date
        self.currency = currency
        self.value = value
        self.length_of_stay = length_of_stay
        self.temp_id = uuid4().hex

    def to_dict(self):
        return {
            "temp_id": self.temp_id,
            "arrival_date": self.arrival_date,
            "currency": self.currency,
            "value": str(self.value),
            "length_of_stay": self.length_of_stay
        }