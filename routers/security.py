from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from routers.database import cursor
from routers.utils import OAuth2PasswordBearerWithCookie


SECRET_KEY = "YOUR_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="token")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def encrypt_value(password):
    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode()
    return hashed_password


def check_password(username, password):
    query = "SELECT password FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    stored_password = cursor.fetchone()[0]
    return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
