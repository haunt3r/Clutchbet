from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/simulate")
def simulate_match(player1: str, player2: str):
    winner = random.choice([player1, player2])
    return {"winner": winner}