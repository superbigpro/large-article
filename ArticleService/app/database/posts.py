from sqlalchemy import BLOB, Column, Integer, String, DateTime, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base

from database import Base

class Posts(Base):
    __tablename__ = "posts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)  
    content = Column(String, nullable=False)  
    picture = Column(BLOB, nullable=True)  
    last_modified = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc), default=datetime.now(timezone.utc))
    is_modified = Column(Boolean, nullable=False, default=False)
    views = Column(Integer, nullable=False, default=0)
    hearts = Column(Integer, nullable=False, default=0)

    comments = relationship('Comments', back_populates='post')
    user_id = Column(BigInteger, nullable=False)
