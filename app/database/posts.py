from sqlalchemy import BLOB, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base

from database import Base

class Posts(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)  
    content = Column(String, nullable=False)  
    picture = Column(BLOB, nullable=True)  
    last_modified = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc), oncreate=datetime.now(timezone.utc))
    is_modified = Column(Boolean, nullable=False, default=False)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False) 
    user = relationship('User', back_populates='application')  
