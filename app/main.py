from typing import List
import uvicorn
import json
import requests


from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models
from app.crud import item_handler, stock_handler, user_handler
from app.database import SessionLocal, engine
from app.errors import credentials_exception
from app.schemas import auth as auth_schema
from app.schemas import item as item_schema
from app.schemas import stock as stock_schema
from app.schemas import user as user_schema
from app.services.jwt import authenticate_user, create_access_token, get_token_data

models.Base.metadata.create_all(bind=engine)


app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/form")


def get_current_user(db: Session = Depends(get_db), token=Depends(oauth2_scheme)):
    token_data = get_token_data(token)
    email = token_data.username
    user = None
    if email:
        user = user_handler.get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    else:
        return user


@app.post("/login/form", response_model=auth_schema.Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login", response_model=auth_schema.Token)
async def login(form_data: auth_schema.Login, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# below are connect to db from https://fastapi.tiangolo.com/zh/tutorial/sql-databases/?fbclid=IwAR24Upu3VKJcqFxuPZ69REaung2GvVlm_QsH_6HaitCjtmCq9rV4zebKtqA


@app.post("/signup/", response_model=user_schema.User)
def create_user(user: user_schema.UserCreate, db: Session = Depends(get_db)):
    db_user = user_handler.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = user_handler.create_user(db=db, user=user)
    return user


@app.get("/users/", response_model=List[user_schema.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    users = user_handler.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=user_schema.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = user_handler.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=item_schema.Item)
def create_item_for_user(
    item: item_schema.ItemCreate,
    user: user_schema.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return item_handler.create_user_item(db=db, item=item, user_id=user.id)


@app.get("/items/", response_model=List[item_schema.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = item_handler.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/stock/list", response_model=List[stock_schema.Stock])
def get_stocks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stocks = stock_handler.get_stocks(db, skip=skip, limit=limit)
    return stocks


@app.post("/stock/", response_model=stock_schema.Stock)
def create_stock(stock: stock_schema.StockCreate, db: Session = Depends(get_db)):
    db_stock = stock_handler.get_stock_by_symbol_id(db, symbol_id=stock.symbolId)
    if db_stock:
        raise HTTPException(status_code=400, detail="SymbolId already registered")
    stock_in_db: stock_schema.Stock = stock_handler.create_stock(db, stock)
    return stock_in_db


@app.post("/user/likes/{symbol_id}")
def add_favorate_stock_to_user(
    symbol_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db_stock = stock_handler.get_stock_by_symbol_id(db, symbol_id=symbol_id)
    if db_stock is None:
        raise HTTPException(status_code=400, detail="Stock does not exist.")
    user.stocks.append(db_stock)
    db.commit()
    return {"success": True}


@app.delete("/user/dislike/{symbol_id}")
def remove_favorate_stock_from_user(
    symbol_id: str,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    db_stock = stock_handler.get_stock_by_symbol_id(db, symbol_id=symbol_id)
    if db_stock is None:
        raise HTTPException(status_code=400, detail="Stock does not exist.")
    if db_stock in user.stocks:
        user.stocks.remove(db_stock)
        db.commit()
    else:
        raise HTTPException(status_code=400, detail="Stock not in favorite list.")
    return {"success": True}


@app.get("/user/likes/list")
def get_user_likes(
    db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    db_stocks = user_handler.get_stocks_by_user(db, user_id=user.id)
    return {"stocks": db_stocks}

@app.get("/search/meta/{symbolId}")
async def search_meta(symbolId):
    header = \
    {"Content-Type": "application/json;charset=UTF-8"}

    body = \
    {
        "query":{
                "term":{
                        "symbolId":{
                                "value": symbolId
                        }
                }
        }
    }
    body_json = json.dumps(body)
    res = requests.post('http://clip3.cs.nccu.edu.tw:9200/meta/_search/',headers=header,data=body_json)
    if res.status_code!=200:
        raise HTTPException(status_code=res.status_code, detail="Stock not found")
    return res.json()['hits']['hits']['source']

@app.get("/search/chart/{symbolId}")
async def search_chart(symbolId):
    header = \
    {"Content-Type": "application/json;charset=UTF-8"}

    body = \
    {
        "query":{
                "term":{
                        "symbolId":{
                                "value": symbolId
                        }
                }
        }
    }
    body_json = json.dumps(body)
    res = requests.post('http://clip3.cs.nccu.edu.tw:9200/chart/_search/',headers=header,data=body_json)
    if res.status_code!=200:
        raise HTTPException(status_code=res.status_code, detail="Stock not found")
    return res.json()['hits']['hits']

if __name__ == '__main__':
    uvicorn.run(app='main:app', host="127.0.0.1", port=8000, reload=True, debug=True)
