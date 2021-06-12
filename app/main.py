from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app import models
from app.crud import item_handler, user_handler
from app.database import SessionLocal, engine
from app.errors import credentials_exception
from app.schemas import auth as auth_schema
from app.schemas import item as item_schema
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


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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


@app.post("/login", response_model=auth_schema.Token)
async def login(form_data: auth_schema.LoginForm, db: Session = Depends(get_db)):
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
