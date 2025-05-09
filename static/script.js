let lastMatchId = localStorage.getItem("lastMatchId") || null;
let accessToken = "";
let loggedInUsername = "";

function printOutput(message) {
  console.log("DOM-UTSKRIFT:", message);
  const outputDiv = document.getElementById("output");
  if (outputDiv) {
    outputDiv.innerText = message;
  } else {
    console.log("Fel: kunde inte hitta output-diven.");
  }
}

// Registrera ny användare
async function registerUser() {
  const username = document.getElementById("reg-username").value;
  const password = document.getElementById("reg-password").value;

  const res = await fetch("/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ username, password })
  });

  const data = await res.json();
  if (res.ok) {
    printOutput("Registrering: " + data.message);
  } else {
    printOutput("Registrering misslyckades: " + data.detail);
  }
}

// Logga in användare
async function loginUser() {
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  const res = await fetch("/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  });

  const data = await res.json();
  if (res.ok) {
    accessToken = data.access_token;
    loggedInUsername = username;
    printOutput(`Inloggning lyckades!\nInloggad som: ${loggedInUsername}`);
  } else {
    printOutput("Inloggning misslyckades: " + (data.detail || JSON.stringify(data)));
  }
}

// Gå med i match
async function joinMatch() {
  const betInput = document.getElementById("bet-amount");
  const modeInput = document.getElementById("game-mode");

  if (!betInput || !modeInput) {
    printOutput("Insatsfält eller spelläge saknas.");
    return;
  }

  const amount = parseInt(betInput.value);
  const mode = modeInput.value;

  if (!amount || isNaN(amount)) {
    printOutput("Ange en giltig insats.");
    return;
  }

  const res = await fetch("/match", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + accessToken
    },
    body: JSON.stringify({
      username: loggedInUsername,
      bet: amount,
      mode: mode
    })
  });

  const data = await res.json();
  console.log("Svar från backend:", data);

  if ("match_id" in data && data.match_id !== null) {
    lastMatchId = data.match_id;
    localStorage.setItem("lastMatchId", data.match_id);
    const message = `Matchstatus: ${data.message} (ID: ${data.match_id})`;
    console.log("UTSKRIFT TILL DOMEN:", message);
    console.log("TEST-DEBUG:", message);
    printOutput(message);
  } else {
    printOutput("Matchfel: " + (data.detail || JSON.stringify(data)));
  }
}

// Visa matchhistorik
async function showHistory() {
  const res = await fetch(`/match/history?username=${loggedInUsername}`, {
    method: "GET",
    headers: {
      "Authorization": "Bearer " + accessToken
    }
  });

  const data = await res.json();

  if (res.ok && data.match && data.match.length > 0) {
    let list = "Matchhistorik:\n";
    for (const [p1, p2] of data.match) {
      list += `${p1} vs ${p2}\n`;
    }
    printOutput(list);
  } else {
    printOutput("Ingen matchhistorik hittades.");
  }
}

// Rapportera resultat
async function submitResult(won) {
  try {
    const matchId = lastMatchId || prompt("Ange match-ID:");
    const team = localStorage.getItem("team");

    if (!matchId) {
      printOutput("Match-ID krävs.");
      return;
    }

    if (!team) {
      printOutput("Team saknas. Kan inte rapportera resultat.");
      return;
    }

    const res = await fetch(`/match/result`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + accessToken
      },
      body: JSON.stringify({
        username: loggedInUsername,
        match_id: matchId,
        won: won
      })
    });

    const data = await res.json();
    if (res.ok && data && data.message) {
      let statusText = "";
      if (data.status) { 
        const teamA = data.status.team_a.join(", ");
        const teamB = data.status.team_b.join(", ");
        statusText = `\n\nRapporterade spelare:\nLag A: ${teamA || "Inga"}\nLag B: ${teamB || "Inga"}`;
      }
      printOutput(data.message + statusText);
    } else {
      printOutput("Fel vid rapportering: " + JSON.stringify(data || { info: "Inget svar från servern" }));
    }
  } catch (error) {
    printOutput("Nätverksfel: " + error.message);
  }
}

function reportWin() {
  submitResult(true);
}

function reportLoss() {
  submitResult(false);
}
function printOutput(text) {
  console.log("DOM-UTSKRIFT:", text);
  const outputDiv = document.getElementById("output");
  if (outputDiv) {
      outputDiv.innerText = text;
  }
}
// Koppla funktionerna till fönstret
window.onload = () => {
  window.loginUser = loginUser;
  window.joinMatch = joinMatch;
  window.submitResult = submitResult;
  window.reportWin = reportWin;
  window.reportLoss = reportLoss;
  window.registerUser = registerUser;
  window.fetchFaceitInfo = fetchFaceitInfo;
  document.getElementById("team-select").addEventListener("change", (e) => {
    localStorage.setItem("team", e.target.value);
  });
}
async function fetchFaceitInfo() {
  const nickname = document.getElementById("faceit-nickname").value;
  const resultDiv = document.getElementById("faceit-result");

  if (!nickname) {
    resultDiv.innerHTML = "<p>Ange ett nickname.</p>";
    return;
  }

  try {
    const response = await fetch(`/faceit-user/${nickname}`);
    if (!response.ok) throw new Error("Kunde inte hämta spelarinformation.");

    const data = await response.json();

    const info = `
      <strong>Nickname:</strong> ${data.nickname}<br>
      <strong>Land:</strong> ${data.country}<br>
      <strong>Spelnivå:</strong> ${data.games.cs2?.skill_level || "Okänd"}<br>
      <strong>Faceit Elo:</strong> ${data.games.cs2?.faceit_elo || "Okänt"}
    `;

    resultDiv.innerHTML = info;
    const profileLink = document.getElementById("faceit-profile-link");
profileLink.href = `https://www.faceit.com/en/players/${data.nickname}`;
profileLink.style.display = "inline-block";
  } catch (error) {
    resultDiv.innerHTML = `<p style="color:red;">${error.message}</p>`;
  }
} 