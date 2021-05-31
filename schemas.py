from typing import List, Optional


from pydantic import BaseModel




class ItemBase(BaseModel):

    title: str

    description: Optional[str] = None




class ItemCreate(ItemBase):

    pass



class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        orm_mode = True


class UserInDB(User):
    hashed_password: str


class UserBase(BaseModel):

    email: str




class UserCreate(UserBase):

    password: str
