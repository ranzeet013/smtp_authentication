from sqlalchemy import Column, String, Integer, BigInteger, Boolean
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4

Base = declarative_base()

class User(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, default=lambda: str(uuid4()), unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    access_token = Column(String, nullable=True)
    expiration = Column(BigInteger, nullable=True)
    otp = Column(String, nullable=True)
    otp_expiration = Column(BigInteger, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)



