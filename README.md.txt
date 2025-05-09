# Clutchbetkod

Detta är ett FastAPI-baserat matchmaking-projekt där användare kan registrera sig, logga in och paras ihop i matcher.

## Steg-för-steg: Starta projektet

### 1. Klona eller kopiera projektmappen till din dator

Navigera sedan till mappen i terminalen:

```bash
cd clutchbetkod

Skapa ett virtuellt environment (valfritt men rekommenderat)

python -m venv venv
venv\Scripts\activate

Installera alla nödvändiga paket:
pip install -r requirements.txt

Starta FastAPI-servern:
uvicorn main:app --reload

Öppna webbläsaren och gå till:
http://127.0.0.1:8000/docs

Funktioner

/auth/register – Registrera en ny användare

/auth/login – Logga in och få en token

/auth/me – Se vem du är (kräver token)

/match/join – Gå med i match-kö (kräver token)

/match/history – Visa alla matcher (kräver token)


Tips

Registrera två användare.

Logga in som båda och klicka på "Authorize" i docs.

Använd /match/join två gånger för att skapa en match.