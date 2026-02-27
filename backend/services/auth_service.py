from backend.core.security import create_access_token, hash_password, verify_password
from backend.repositories.auth_repo import AuthRepository
from backend.schemas.auth_schema import AuthOut, ChangePasswordIn, LoginIn, RegisterIn, RegisterOut


class AuthValidationError(ValueError):
    pass


class AuthConflictError(ValueError):
    pass


class AuthUnauthorizedError(ValueError):
    pass


class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _validate_password_strength(password: str) -> None:
        if len(password) < 8:
            raise AuthValidationError("Password must be at least 8 characters long.")

    def register(self, payload: RegisterIn) -> RegisterOut:
        email = self._normalize_email(payload.email)
        self._validate_password_strength(payload.password)

        if self.repo.get_user_by_email(email):
            raise AuthConflictError("A user with this email already exists.")

        user = self.repo.create_user(
            email=email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        return RegisterOut(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            message="User created successfully.",
        )

    def login(self, payload: LoginIn) -> AuthOut:
        email = self._normalize_email(payload.email)
        user = self.repo.get_user_by_email(email)

        if not user or not verify_password(payload.password, user.password_hash):
            raise AuthUnauthorizedError("Invalid email or password.")
        if not user.is_active:
            raise AuthUnauthorizedError("User account is inactive.")

        token = create_access_token(subject=user.email, role=user.role, user_id=str(user.id))
        return AuthOut(access_token=token, user_id=str(user.id), role=user.role)

    def change_password(self, user_id, payload: ChangePasswordIn) -> None:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise AuthUnauthorizedError("User not found.")
        if not verify_password(payload.current_password, user.password_hash):
            raise AuthUnauthorizedError("Current password is incorrect.")
        self._validate_password_strength(payload.new_password)
        if payload.current_password == payload.new_password:
            raise AuthValidationError("New password must be different from current password.")

        self.repo.update_password(user.id, hash_password(payload.new_password))
