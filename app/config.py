import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User

token = os.environ.get("OperChatBotToken")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename="db/log.log",
)

logger = logging.getLogger("manual")

engine = create_engine('sqlite:///db/botdb.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

superusers = ["MityaiS", "av_shatrov", "shefoff"]

session = Session()
for username in superusers:
    user = session.query(User).filter_by(username=username).first()
    if not user:
        new_user = User(username=username, superuser=True)
        session.add(new_user)
        session.commit()
        logger.info(f"Added {username} to superusers")
session.close()
