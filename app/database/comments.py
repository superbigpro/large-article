from sqlalchemy import BLOB, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.ext.declarative import declarative_base

from database import Base

class Comments(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(String, nullable=False) 
    last_modified = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc), default=datetime.now(timezone.utc))
    is_modified = Column(Boolean, nullable=False, default=False)
    
    post_id = Column(String, ForeignKey('posts.id'), nullable=False)
    post = relationship('Posts', back_populates='comments')

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False) 
    user = relationship('User', back_populates='posts')  
