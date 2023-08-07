from models import User
from config import logger


def user_exists(username, session):
    existing_user = session.query(User).filter_by(username=username).first()
    return existing_user is not None


def add_user_to_db(username, session):
    user_db = User(username=username)
    session.add(user_db)
    session.commit()


def get_all_users(session):
    return session.query(User).all()


def remove_users_from_db(usernames, session):

    results = []

    for username in usernames:
        user = session.query(User).filter_by(username=username).first()

        if user:
            session.delete(user)
            session.commit()
            results.append(f"Пользователь '{username}' был удален из белого листа.")
            logger.info(f"{username} was removed from white list")
        else:
            results.append(f"Пользователь '{username}' не был найден в белом листе.")

    return results


def is_superuser(username, session):
    user = session.query(User).filter_by(username=username).first()
    return user is not None and user.superuser
