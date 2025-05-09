from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from security import hash_password, verify_password, create_access_token, verify_token

router = APIRouter()

# Enkel användardatabas i minnet
fake_users_db = {}

class User(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Användarnamn upptaget")
    hashed = hash_password(user.password)
    fake_users_db[user.username] = hashed
    return {"message": "Registrerad!"}

@router.post("/login")
def login(user: User):
    hashed_pw = fake_users_db.get(user.username)
    if not hashed_pw or not verify_password(user.password, hashed_pw):
        raise HTTPException(status_code=401, detail="Felaktig inloggning")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
def get_me(username: str = Depends(verify_token)):
    return {"username": username}