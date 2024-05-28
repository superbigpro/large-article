from sqlalchemy import BLOB, Column, Integer, String, DateTime, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base

from database import Base

class Posts(Base):
    __tablename__ = "posts"
    # 고유 id 
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 제목 
    title = Column(String, nullable=False)  
    content = Column(String, nullable=False)  
    picture = Column(BLOB, nullable=True)  
    last_modified = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc), default=datetime.now(timezone.utc))
    is_modified = Column(Boolean, nullable=False, default=False)

    comments = relationship('Comments', back_populates='post')
    user_id = Column(BigInteger, nullable=False)
