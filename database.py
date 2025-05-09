# Simpel databasmock - i riktig miljö: använd SQLite eller PostgreSQL
users = {}
matches = []


def add_user(username, password):
    users[username] = password

def record_match(player1, player2, winner):
    matches.append({"p1": player1, "p2": player2, "winner": winner})