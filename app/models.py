import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table, DateTime
from sqlalchemy.orm import relationship

from .database import Base

favorites_table = Table('favorites', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('stock_id', Integer, ForeignKey('stocks.id')),
    Column('created_at', DateTime, default=datetime.datetime.utcnow)
)
class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    items = relationship("Item", back_populates="owner")
    stocks = relationship(
        "Stock",
        secondary=favorites_table,
        back_populates="users")



class Item(Base):

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    isIndex = Column(Boolean, index=True)
    nameZhTw = Column(String, index=True)
    industryZhTw = Column(String, index=True)
    abnormal = Column(String, index=True)
    mode = Column(String, index=True)
    symbolId = Column(String, index=True, unique=True)
    countryCode = Column(String, index=True)
    timeZone = Column(String, index=True)

    users = relationship(
        "User",
        secondary=favorites_table,
        back_populates="stocks")