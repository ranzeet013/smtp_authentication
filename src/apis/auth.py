from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from schemas.user_schemas import ChangePassword, UserCreate, UserLogin, UserOut, Token, OTPVerify
from services.auth_service import change_user_password, create_user, authenticate_user, delete_user, verify_otp
from configs.auth_config import get_db
from tools.auth_tools import get_current_user
from models.user_models import User

router = APIRouter()

@router.get("/ping")
async def ping():
    """
    Health check endpoint.
    Returns a simple 'pong' message to confirm the API is running.
    """
    return {"message": "pong from onboarding"}

@router.post("/register", response_model=UserOut, tags=["Authentication"])
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and send OTP for email verification.
    Request Body: UserCreate (name, email, password)
    Response: UserOut (uuid, name, email, is_verified)
    Raises: HTTP 400 if email is already registered
    """
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user = await create_user(db, user)
    return db_user

@router.post("/verify-otp", response_model=UserOut, tags=["Authentication"])
async def verify_otp_endpoint(otp_data: OTPVerify, db: AsyncSession = Depends(get_db)):
    """
    Verify OTP sent to user's email.
    Request Body: OTPVerify (email, otp)
    Response: UserOut (uuid, name, email, is_verified)
    Raises: HTTP 404 if user not found, HTTP 400 if OTP is invalid or expired
    """
    return await verify_otp(db, otp_data)

@router.post("/login", response_model=Token, tags=["Authentication"])
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.
    Request Body: UserLogin (email, password)
    Response: Token (access_token, token_type)
    Raises: HTTP 401 if credentials are invalid, HTTP 403 if email not verified
    """
    db_user = await authenticate_user(db, user.email, user.password)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return db_user

@router.get("/users/me", response_model=UserOut, tags=["Authentication"])
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current authenticated user's details.
    Requires: Bearer token in Authorization header
    Response: UserOut (uuid, name, email, is_verified)
    Raises: HTTP 401 if token is invalid or user not found
    """
    return current_user

@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT, tags=["Authentication"])
async def delete_user_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Delete the current authenticated user's account.
    Requires: Bearer token in Authorization header
    Response: No content
    Raises: HTTP 401 if token is invalid or user not found
    """
    await delete_user(db, current_user)
    return None

@router.put("/users/me/password", response_model=UserOut, tags=["Authentication"])
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the current authenticated user's password.
    Request Body: ChangePassword (current_password, new_password)
    Response: UserOut (uuid, name, email, is_verified)
    Raises: HTTP 401 if current password is invalid, HTTP 400 if new password is invalid
    """
    updated_user = await change_user_password(db, current_user, password_data)
    return updated_user