from fastapi import APIRouter, status

from backend.modules.auth.auth_schema import LoginResponse, LoginUser, RegisterResponse, RegisterUser

auth_router = APIRouter()


@auth_router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user: RegisterUser):
    pass


@auth_router.post("/login", response_model=LoginResponse)
async def login(user: LoginUser):
    pass
