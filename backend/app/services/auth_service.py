"""
Authentication service — business logic for registration, login, and user validation.
"""

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.logging import log_auth_event


class AuthService:
    """Handles authentication business logic."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register(self, name: str, email: str, password: str) -> tuple[User, str]:
        """
        Register a new user.

        Returns:
            Tuple of (User, access_token)

        Raises:
            BadRequestError: If email already exists.
        """
        existing = self.repo.get_by_email(email)
        if existing:
            log_auth_event("REGISTER", email, success=False)
            raise BadRequestError(
                code="EMAIL_ALREADY_EXISTS",
                message="A user with this email already exists.",
            )

        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.INSPECTOR,
        )
        user = self.repo.create(user)

        token = create_access_token(subject=str(user.id))
        log_auth_event("REGISTER", email, success=True)
        return user, token

    def login(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate a user.

        Returns:
            Tuple of (User, access_token)

        Raises:
            UnauthorizedError: If credentials are invalid.
        """
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            log_auth_event("LOGIN", email, success=False)
            raise UnauthorizedError(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )

        token = create_access_token(subject=str(user.id))
        log_auth_event("LOGIN", email, success=True)
        return user, token
