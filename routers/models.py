from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str | None = None


class User(BaseModel):
    id: str
    username: str
    is_admin: bool
