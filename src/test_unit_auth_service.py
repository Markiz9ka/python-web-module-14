import unittest
import asyncio
from unittest.mock import MagicMock, patch
from jose import jwt, JWTError
import datetime
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from auth.service import Auth
from auth.models import User
from contacts.schema import Contacts
from auth.exceptions import AuthException

class TestAuth(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.auth = Auth()
        self.auth.HASH_CONTEXT = CryptContext(schemes=["bcrypt"])
        self.auth.ALGORITHM = "HS256"
        self.auth.SECRET = "testsecret"
        self.user = User(username="testuser", refresh_token="some_token")
    
    def test_verify_password(self):
        plain_password = "password123"
        hashed_password = self.auth.HASH_CONTEXT.hash(plain_password)
        result = self.auth.verify_password(plain_password, hashed_password)
        self.assertTrue(result)

    def test_hash_password(self):
        plain_password = "password123"
        hashed_password = self.auth.hash_password(plain_password)
        self.assertTrue(self.auth.HASH_CONTEXT.verify(plain_password, hashed_password))

    @patch('auth.service.datetime')
    @patch('jose.jwt.encode')
    async def test_create_access_token(self, mock_jwt_encode, mock_datetime):
        mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        mock_jwt_encode.return_value = "test_access_token"
        
        payload = {"sub": "testuser"}
        token = await self.auth.create_access_token(payload)
        
        self.assertEqual(token, "test_access_token")
        mock_jwt_encode.assert_called_once()

    @patch('auth.service.datetime')
    @patch('jose.jwt.encode')
    async def test_create_refresh_token(self, mock_jwt_encode, mock_datetime):
        mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
        mock_jwt_encode.return_value = "test_refresh_token"
        
        payload = {"sub": "testuser"}
        token = await self.auth.create_refresh_token(payload)
        
        self.assertEqual(token, "test_refresh_token")
        mock_jwt_encode.assert_called_once()

    @patch('jose.jwt.decode')
    @patch('database.get_database')
    def test_get_user_valid_token(self, mock_get_database, mock_jwt_decode):
        mock_jwt_decode.return_value = {"sub": "testuser", "scope": "access_token"}
        mock_db = MagicMock()
        mock_get_database.return_value = mock_db
        mock_db.query().filter().first.return_value = self.user
        
        user = self.auth.get_user(token="valid_token", db=mock_db)
        
        self.assertEqual(user, self.user)

    @patch('jose.jwt.decode', side_effect=JWTError("Invalid token"))
    def test_get_user_invalid_token(self, mock_jwt_decode):
        with self.assertRaises(AuthException):
            self.auth.get_user(token="invalid_token")
    
    @patch('jose.jwt.decode')
    @patch('database.get_database')
    def test_get_user_no_refresh_token(self, mock_get_database, mock_jwt_decode):
        mock_jwt_decode.return_value = {"sub": "testuser", "scope": "access_token"}
        mock_db = MagicMock()
        mock_get_database.return_value = mock_db
        self.user.refresh_token = None
        mock_db.query().filter().first.return_value = self.user
        
        with self.assertRaises(AuthException):
            self.auth.get_user(token="valid_token", db=mock_db)

if __name__ == "__main__":
    unittest.main()
