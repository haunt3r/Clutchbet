from pydantic import BaseModel

class Match(BaseModel):
    player1: str
    player2: str
    winner: str