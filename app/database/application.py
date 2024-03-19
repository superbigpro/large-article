from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

from database import Base

class Application(Base):
    __tablename__ = "application"
    id = Column(Integer, primary_key=True, autoincrement=True)
    bio = Column(String, nullable=False)  
    motive = Column(String, nullable=False)  
    plan = Column(String, nullable=False)  
    last_modified = Column(DateTime, nullable=True, onupdate=datetime.utcnow, default=datetime.utcnow)
    is_submitted = Column(Boolean, nullable=False, default=False)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False) 
    user = relationship('User', back_populates='application')  

    department_id = Column(Integer, ForeignKey('department.id'), nullable=True)  # department 테이블의 id를 참조
    department = relationship('Department', back_populates='application')  # back_populates 속성명을 복수형으로 변경

