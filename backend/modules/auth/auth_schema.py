from pydantic import BaseModel


class RegisterUser(BaseModel):
    name: str
    email: str
    password: str


class RegisterResponse(BaseModel):
    id: str
    name: str
    email: str


class LoginUser(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
