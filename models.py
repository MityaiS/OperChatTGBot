from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    superuser = Column(Boolean, default=False)

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', superuser={self.superuser})"
