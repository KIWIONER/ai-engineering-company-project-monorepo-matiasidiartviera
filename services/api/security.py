import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
from dotenv import load_dotenv
from jose import jwt
from passlib.hash import bcrypt

load_dotenv()
_WEAK_DEFAULTS = {
    "",
    "mi_clave_secreta_super_segura_que_nadie_sabe",
    "tu_clave_secreta_aqui_cambiar_en_produccion",
}

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if SECRET_KEY in _WEAK_DEFAULTS:
    if "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") or os.getenv("APP_ENV") == "test":
        # En tests sin .env se genera una clave aleatoria efímera por ejecución (nunca predecible)
        SECRET_KEY = secrets.token_urlsafe(32)
    else:
        raise RuntimeError(
            "SECRET_KEY no está configurado o usa un valor inseguro. "
            "Defínelo en .env o como variable de entorno."
        )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_password_hash(password: str) -> str:
    return bcrypt.hash(password)