import os
import uuid
from tinydb import TinyDB, Query
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv

load_dotenv()

# 1. CONFIGURACIÓN DE SUPABASE (SQLModel)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("La variable DATABASE_URL no está configurada en el .env")


engine = create_engine(DATABASE_URL, echo=True)

def get_db():
    with Session(engine) as session:
        yield session

# 2. CONFIGURACIÓN DE TINYDB (Auth Existente)
DB_FILE = os.path.join(os.path.dirname(__file__),'data', 'suppliers_db.json')
def get_tinydb() -> TinyDB:
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    return TinyDB(DB_FILE)

# --- Funciones de Usuarios y Tokens ---

def get_user_by_email(email:str):
    db = get_tinydb()
    users_table = db.table('users')
    userQuery = Query()
    result = users_table.search(userQuery.email == email)
    if result:
        return result[0]
    return None

def get_user_by_id(user_id:str):
    db = get_tinydb()
    user_table = db.table('users')
    userQuery = Query()
    result = user_table.search(userQuery.id == user_id)
    if result:
        return result[0]
    return None
def create_user_in_db(user_data:dict, profile_data:dict):
    db = get_tinydb()
    users_table = db.table('users')
    profiles_table = db.table('profiles')

    user_id = str(uuid.uuid4())
    user_data['id'] = user_id

    profile_data['id']= str(uuid.uuid4())
    profile_data['user_id'] = user_id

    users_table.insert(user_data)
    profiles_table.insert(profile_data)
    return user_data, profile_data


def save_reset_token(email: str, token_hash: str, expires_at: float):
    db = get_tinydb()
    tokens_table = db.table('reset_tokens')
    tokens_table.insert({
        'email': email,
        'token_hash': token_hash,
        'expires_at': expires_at,
        'used': False
    })


def get_reset_token(token_hash: str):
    db = get_tinydb()
    tokens_table = db.table('reset_tokens')
    tokenQuery = Query()
    result = tokens_table.search(tokenQuery.token_hash == token_hash)
    if result:
        return result[0]
    return None
def mark_token_used(token_hash: str):
    db = get_tinydb()
    tokens_table = db.table('reset_tokens')
    tokenQuery = Query()
    tokens_table.update({'used': True}, tokenQuery.token_hash == token_hash)
