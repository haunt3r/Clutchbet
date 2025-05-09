from fastapi import Form
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from fastapi.responses import RedirectResponse
import urllib.parse
load_dotenv("4bfe051f-ff08-48f2-9edb-67a7724c2629")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
class ResultReport(BaseModel):
    username: str
    match_id: int
    won: bool
import secrets
from fastapi.responses import HTMLResponse
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
app = FastAPI()
@app.middleware("http")
async def redirect_www(request: Request, call_next):
    host = request.headers.get("host", "")
    if host.startswith("www."):
        url = str(request.url).replace("://www.", "://")
        return RedirectResponse(url)
    response = await call_next(request)
    return response
FACEIT_API_KEY = "4bfe051f-ff08-48f2-9edb-67a7724c2629"

@app.get("/faceit-user/{nickname}")
async def get_faceit_user_info(nickname: str):
    url = f"https://open.faceit.com/data/v4/players?nickname={nickname}"
    headers = {
        "Authorization": f"Bearer {FACEIT_API_KEY}"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Kunde inte hämta användarinformation")

    return response.json()



@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# === Autentisering ===
security = HTTPBearer()
tokens = {}
users = {}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in tokens.values():
        raise HTTPException(status_code=401, detail="Ogiltig token")
    return token

# === Modeller ===
class User(BaseModel):
    username: str
    password: str

class MatchRequest(BaseModel):
    username: str
    bet: int
    mode: str  # "1v1" eller "5v5"

class ResultReport(BaseModel):
    username: str
    match_id: int
    won: bool

# === Data ===
waiting_player = None
team_a = []
team_b = []
matches = []

# === Endpoints ===

@app.post("/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(status_code=400, detail="Användarnamnet är redan taget.")
    users[user.username] = user.password
    return {"message": "Registrering lyckades"}

@app.post("/token")
def login(username: str = Form(...), password: str = Form(...)):
    if username not in users or users[username] != password:
        raise HTTPException(status_code=401, detail="Felaktigt användarnamn eller lösenord.")
    token = secrets.token_hex(16)
    tokens[username] = token
    return {"access_token": token, "token_type": "bearer"}

@app.post("/match")
def join_match(req: MatchRequest):
    global waiting_player, team_a, team_b
    username = req.username

    if req.username not in users:
        raise HTTPException(status_code=404, detail="Användare hittades inte.")

    # Kontroll: Spelaren får inte vara med i någon pågående match
    for match in matches:
        if username in match.get("team_a", []) or \
           username in match.get("team_b", []) or \
           username == match.get("player1") or \
           username == match.get("player2"):
            raise HTTPException(status_code=400, detail="Du är redan med i en match.")

    if req.mode == "1v1":
        if waiting_player is None:
            waiting_player = {
                "username": req.username,
                "bet": req.bet,
                "mode": "1v1"
            }
            return {
                "message": "Väntar på motståndare...",
                "match_id": len(matches)  # nästa ID blir detta
            }
        else:
            match = {
                "player1": waiting_player["username"],
                "player2": req.username,
                "bet": waiting_player["bet"],
                "mode": "1v1",
                "winner": None
            }
            matches.append(match)
            waiting_player = None
            return {
                "message": "1v1-match skapad!",
                "match": match,
                "match_id": len(matches) - 1
            }

    elif req.mode == "5v5":
        if len(team_a) < 5:
            team_a.append(req.username)
            match = {
                "mode": "5v5",
                "team_a": team_a.copy(),
                "team_b": team_b.copy(),
                "winner": None,
                "bet": req.bet,
                "resultat": {
                    "team_a": [],
                    "team_b": []
                }
            }
            match_id = len(matches)
            matches.append(match)
            return {
                "message": f"Spelare tillagd i Team A ({len(team_a)}/5). Väntar på fler...",
                "match_id": match_id
            }

        elif len(team_b) < 5:
            team_b.append(req.username)
            match = {
                "mode": "5v5",
                "team_a": team_a.copy(),
                "team_b": team_b.copy(),
                "winner": None,
                "bet": req.bet,
                "resultat": {
                    "team_a": [],
                    "team_b": []
                }
            }
            match_id = len(matches)
            matches.append(match)
            return {
                "message": f"Spelare tillagd i Team B ({len(team_b)}/5). Väntar på fler...",
                "match_id": match_id
            }

        else:
            raise HTTPException(status_code=400, detail="Båda lagen är redan fulla.")

    else:
        raise HTTPException(status_code=400, detail="Ogiltigt spelläge.")

def payout_to_team(team):
    payout_amount = 90  # Exempel: 100 kr insats - 10% avgift
    for player in team:
        print(f"Payout till {player}: {payout_amount} kr")  # Byt ut med riktig saldohantering senare
@app.post("/match/result")
def submit_result(data: ResultReport, token: str = Depends(verify_token)):
    username = data.username
    match_id = data.match_id
    won = data.won

    if match_id >= len(matches):
        raise HTTPException(status_code=404, detail="Match-ID finns inte.")

    match = matches[match_id]

    if match["winner"] is not None:
        return {"message": f"Matchen är redan avgjord. Vinnare: {match['winner']}"}

    # === 1v1-logik ===
    if match["mode"] == "1v1":
        if username not in [match["player1"], match["player2"]]:
            raise HTTPException(status_code=403, detail="Du deltog inte i matchen.")

        if "resultat" not in match:
            match["resultat"] = {}

        if username in match["resultat"]:
            return {"message": "Du har redan rapporterat resultat."}

        match["resultat"][username] = won

        if len(match["resultat"]) == 2:
            users_in = list(match["resultat"].keys())
            if match["resultat"][users_in[0]] != match["resultat"][users_in[1]]:
                winner = users_in[0] if match["resultat"][users_in[0]] else users_in[1]
                match["winner"] = winner
                return {"message": f"Resultat sparat! Vinnare: {winner}"}
            else:
                return {"message": "Oenigt resultat – ingen vinnare satt."}
        else:
            return {"message": "Ditt resultat är sparat. Väntar på motståndaren."}

    # === 5v5-logik ===
    elif match["mode"] == "5v5":
        if username not in match["team_a"] and username not in match["team_b"]:
            raise HTTPException(status_code=403, detail="Du deltog inte i denna 5v5-match.")

        if "resultat" not in match:
            match["resultat"] = {"team_a": [], "team_b": []}

        team_key = "team_a" if username in match["team_a"] else "team_b"

        if username in match["resultat"][team_key]:
            return {"message": "Du har redan rapporterat resultat."}

        if won:
         match["resultat"][team_key].append(username)

    if len(match["resultat"]["team_a"]) >= 3:
        match["winner"] = "team_a"
        payout_to_team(match["team_a"])
        return {
            "message": "Team A vinner matchen!",
            "status": match["resultat"]
        }
    elif len(match["resultat"]["team_b"]) >= 3:
        match["winner"] = "team_b"
        payout_to_team(match["team_b"])
        return {
            "message": "Team B vinner matchen!",
            "status": match["resultat"]
        }

    return {
        "message": f"Ditt resultat är sparat. Väntar på fler spelare från {team_key}...",
        "status": match["resultat"]
    }
    raise HTTPException(status_code=400, detail="Okänt spelläge.")
@app.get("/login")
def login():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid",
        "state": "clutchbet123"
    }
    url = f"https://accounts.faceit.com/?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)

@app.get("/callback")
async def callback(code: str, state: str):
    token_url = "https://api.faceit.com/auth/v1/oauth/token"
    headers = {"Content-Type": "application/json"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, json=data, headers=headers)

    if token_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Kunde inte hämta access token")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    profile_url = "https://open.faceit.com/data/v4/players"
    profile_headers = {
        "Authorization": f"Bearer {access_token}"
    }

    async with httpx.AsyncClient() as client:
        profile_response = await client.get(profile_url, headers=profile_headers)

    if profile_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Kunde inte hämta spelarprofil")

    profile = profile_response.json()
    return {
        "nickname": profile.get("nickname"),
        "faceit_id": profile.get("player_id"),
        "games": profile.get("games", {})
    }
@app.get("/terms", response_class=HTMLResponse)
def show_terms():
    with open("static/terms.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/privacy", response_class=HTMLResponse)
def show_privacy():
    with open("static/privacy.html", "r", encoding="utf-8") as f:
        return f.read()