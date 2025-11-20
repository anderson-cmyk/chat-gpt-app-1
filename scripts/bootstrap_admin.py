"""Create an initial admin user for the survey app."""
import getpass

from sqlmodel import Session, select

from app.auth import get_password_hash
from app.database import engine, init_db
from app.models import User, Role


def main():
    init_db()
    username = input("Admin username: ")
    password = getpass.getpass("Admin password: ")
    full_name = input("Nome completo (opcional): ")

    with Session(engine) as session:
        if session.exec(select(User).where(User.username == username)).first():
            print("User already exists, skipping")
            return
        user = User(
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name or None,
            role=Role.admin,
            is_active=True,
        )
        session.add(user)
        session.commit()
        print("Admin created")


if __name__ == "__main__":
    main()
