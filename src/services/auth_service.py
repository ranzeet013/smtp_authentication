import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from schemas.user_schemas import ChangePassword, UserCreate, Token, OTPVerify
from tools.auth_tools import get_password_hash, create_access_token, verify_password
from models.user_models import User
from dotenv import load_dotenv
# Load .env from project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Database configuration from environment variables
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

async def send_otp_email(email: str, otp: str):
    msg = MIMEText(f"Your OTP for verification is: {otp}. It is valid for 10 minutes.")
    msg["Subject"] = "Your OTP Verification Code"
    msg["From"] = EMAIL_USER
    msg["To"] = email

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send OTP email: {str(e)}")

async def generate_and_store_otp(db: AsyncSession, user: User):
    otp = "".join(random.choices(string.digits, k=6))
    otp_expiration = int((datetime.utcnow() + timedelta(minutes=10)).timestamp())
    user.otp = otp
    user.otp_expiration = otp_expiration
    await db.commit()
    await db.refresh(user)
    await send_otp_email(user.email, otp)
    return otp

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    await generate_and_store_otp(db, db_user)
    return db_user

async def verify_otp(db: AsyncSession, otp_data: OTPVerify):
    result = await db.execute(select(User).filter(User.email == otp_data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")
    if not user.otp or user.otp != otp_data.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
    if user.otp_expiration < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")
    user.is_verified = True
    user.otp = None
    user.otp_expiration = None
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    access_token, expiration = create_access_token(
        {"uuid": str(user.uuid), "email": user.email}
    )
    user.access_token = access_token
    user.expiration = expiration
    await db.commit()
    return {"access_token": access_token, "token_type": "bearer"}

async def delete_user(db: AsyncSession, user: User):
    db.delete(user)
    await db.commit()

async def change_user_password(db: AsyncSession, user: User, password_data: ChangePassword):
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    if len(password_data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be at least 6 characters long")
    user.hashed_password = get_password_hash(password_data.new_password)
    user.access_token = None
    user.expiration = None
    await db.commit()
    await db.refresh(user)
    return user