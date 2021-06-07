from sqlalchemy.orm import Session

from app import models
from app.schemas import user as user_schema
from app.services.jwt import get_password_hash


def get_user(db: Session, user_id: int):

    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_password(db: Session, password: str):

    return db.query(models.User).filter(models.User.hashed_password == password).first()


def get_user_login(db: Session, email: str):

    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_email(db: Session, email: str):

    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):

    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: user_schema.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.email, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
