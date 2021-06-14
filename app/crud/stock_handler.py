from sqlalchemy.orm import Session

from app import models
from app.schemas import stock as stock_schema


def get_stock(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Stock).offset(skip).limit(limit).all()


def create_stock(db: Session, stock: stock_schema.StockCreate):
    stock_in_db = models.Stock(**stock.dict())
    db.add(stock_in_db)
    db.commit()
    db.refresh(stock_in_db)
    return stock_in_db


def get_stock_by_symbol_id(db: Session, symbol_id: str):

    return db.query(models.Stock).filter(models.Stock.symbolId == symbol_id).first()
