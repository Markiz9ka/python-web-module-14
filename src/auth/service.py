import jose.jwt
import typing
import fastapi
import fastapi.security
import datetime
import passlib.context
import os
from dotenv import load_dotenv
load_dotenv()
import auth.models
import auth.exceptions
import database

class Auth:
    """
    The Auth class manages authentication, including password hashing,
    JWT token generation, and validation.
    """
    HASH_CONTEXT = passlib.context.CryptContext(schemes=["bcrypt"])
    ALGORITHM = os.environ.get('ALGORITHM')
    SECRET = os.environ.get('SECRET_KEY')
    oauth2_schema = fastapi.security.OAuth2PasswordBearer("/auth/login")

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:
        """
        Verifies if the provided plain password matches the hashed password.

        Args:
            plain_password (str): The plain password provided by the user.
            hashed_password (str): The hashed password stored in the database.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        return self.HASH_CONTEXT.verify(plain_password, hashed_password)

    def hash_password(self, plain_password: str) -> str:
        """
        Hashes the given plain password.

        Args:
            plain_password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        return self.HASH_CONTEXT.hash(plain_password)

    async def create_access_token(
        self, payload: dict[str, typing.Any]
    ) -> str:
        """
        Creates a JWT access token with a 15-minute expiration time.

        Args:
            payload (dict[str, typing.Any]): The data for the token, including the user.

        Returns:
            str: The generated JWT token.
        """
        current_time = datetime.datetime.now(datetime.timezone.utc)
        expire_time = current_time + datetime.timedelta(minutes=15)

        payload.update({
            "iat": current_time,
            "exp": expire_time,
            "scope": "access_token"
        })

        jwt_token = jose.jwt.encode(
            payload, self.SECRET, self.ALGORITHM
        )

        return jwt_token


    async def create_refresh_token(
        self, payload: dict[str, typing.Any]
    ) -> str:
        """
        Creates a JWT refresh token with a 7-day expiration time.

        Args:
            payload (dict[str, typing.Any]): The data for the token, including the user.

        Returns:
            str: The generated JWT refresh token.
        """
        current_time = datetime.datetime.now(datetime.timezone.utc)
        expire_time = current_time + datetime.timedelta(days=7)

        payload.update({
            "iat": current_time,
            "exp": expire_time,
            "scope": "refresh_token"
        })

        jwt_token = jose.jwt.encode(
            payload, self.SECRET, self.ALGORITHM
        )

        return jwt_token

    def get_user(
        self,
        token = fastapi.Depends(oauth2_schema),
        db = fastapi.Depends(database.get_database)
    ) -> auth.models.User:
        """
        Retrieves the user from the database using the JWT access token.

        Args:
            token (str): The JWT token provided by the user.
            db (Session): The database session.

        Returns:
            auth.models.User: The user retrieved from the database.

        Raises:
            AuthException: If the token is invalid, the user is not found, 
                           or the refresh token is not available.
        """
        try:
            payload = jose.jwt.decode(
                token, self.SECRET, algorithms=[self.ALGORITHM]
            )

            if payload['scope'] == "access_token":
                username = payload.get("sub")

                if username is None:
                    raise auth.exceptions.AuthException("Invalid user")

                user = db.query(auth.models.User).filter(auth.models.User.username==username).first()
                if user is None:
                    raise auth.exceptions.AuthException("No such user")
                
                if user.refresh_token is None:
                    raise auth.exceptions.AuthException("No way")

                return user

            elif payload['scope'] == "refresh_token":
                raise auth.exceptions.AuthException("What are you doing?")
            else:
                raise auth.exceptions.AuthException("Do you know the secret?")
        except jose.JWTError as e:
            raise auth.exceptions.AuthException(e)
