from fastapi import APIRouter, Depends, Body
from security import verify_token

router = APIRouter()

waiting_list = []  # Lista över spelare som väntar
match_history = []  # Lista över matchhistorik


@router.post("/join")
def join_queue(
    username: str = Depends(verify_token),
    stake: int = Body(..., embed=True)
):
    # Kolla om spelaren redan är i kön
    if any(entry["username"] == username for entry in waiting_list):
        return {"message": "Du väntar redan i kön."}

    # Lägg till i kön
    waiting_list.append({"username": username, "stake": stake})

    if len(waiting_list) >= 2:
        p1 = waiting_list.pop(0)
        p2 = waiting_list.pop(0)
        match = {
            "player1": p1["username"],
            "player2": p2["username"],
            "stake": min(p1["stake"], p2["stake"])  # minsta insats vinner
        }
        match_history.append(match)
        return {"message": "Match skapad", "match": match}

    return {"message": "Väntar på fler spelare"}


@router.get("/history")
def get_history(username: str = Depends(verify_token)):
    user_matches = [
        m for m in match_history if username in (m["player1"], m["player2"])
    ]
    return {"match": user_matches}