from typing import List, Optional

from pydantic import BaseModel


class StockBase(BaseModel):
    isIndex: bool
    nameZhTw: str
    industryZhTw: str
    abnormal: str
    mode: str
    symbolId: str
    countryCode: str
    timeZone: str


class StockCreate(StockBase):

    pass


class Stock(StockBase):
    class Config:
        orm_mode = True
