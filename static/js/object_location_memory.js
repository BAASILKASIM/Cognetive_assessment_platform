// ==========================================
// Object Location Memory Task Logic & Navigation
// ==========================================

let currentRound = 0;
let userPlacement = {};
let originalPositions = {};
let timerInterval = null;
let timeLeft = 8;
let selectedIcon = null;
let score = 0;

const memoryGrid = document.getElementById("memoryGrid");
const answerGrid = document.getElementById("answerGrid");
const recallArea = document.getElementById("recallArea");
const iconBank = document.getElementById("iconBank");
const timerDisplay = document.getElementById("timer");
const roundNumberDisplay = document.getElementById("roundNumber");
const startBtn = document.getElementById("startBtn");

// Helper to reliably retrieve CSRF Token
function getCsrfToken() {
    if (typeof csrfToken !== "undefined" && csrfToken) return csrfToken;
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith("csrftoken=")) {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return cookieValue || "";
}

// Bind Start Button
if (startBtn) {
    startBtn.addEventListener("click", startObjectLocationTest);
}

function startObjectLocationTest() {
    currentRound = 0;
    score = 0;
    const instructionCard = document.getElementById("instructionCard");
    const gameArea = document.getElementById("gameArea");
    if (instructionCard) instructionCard.style.display = "none";
    if (gameArea) gameArea.style.display = "block";
    startRound();
}

function startRound() {
    if (timerInterval) clearInterval(timerInterval);

    if (typeof GAME_DATA === "undefined" || !GAME_DATA || currentRound >= GAME_DATA.length) {
        finishGame();
        return;
    }

    userPlacement = {};
    originalPositions = {};
    selectedIcon = null;
    timeLeft = 8;

    if (roundNumberDisplay) roundNumberDisplay.innerText = currentRound + 1;
    if (timerDisplay) timerDisplay.innerText = timeLeft;

    if (recallArea) recallArea.classList.add("d-none");
    if (memoryGrid) {
        memoryGrid.style.display = "grid";
        memoryGrid.innerHTML = "";
    }

    buildGrid();

    // 8-second exposure countdown
    timerInterval = setInterval(() => {
        timeLeft--;
        if (timerDisplay) timerDisplay.innerText = timeLeft;

        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            showRecallPhase();
        }
    }, 1000);
}

function buildGrid() {
    const roundData = GAME_DATA[currentRound];
    if (!roundData) return;

    roundData.forEach(item => {
        originalPositions[item.icon.label] = item.position;
    });

    for (let i = 0; i < 9; i++) {
        const cell = document.createElement("div");
        cell.className = "grid-cell";

        const found = roundData.find(item => item.position === i);
        if (found) {
            cell.innerHTML = `<i class="bi bi-${found.icon.id}"></i>`;
        }

        memoryGrid.appendChild(cell);
    }
}

function showRecallPhase() {
    if (memoryGrid) memoryGrid.style.display = "none";
    if (recallArea) recallArea.classList.remove("d-none");

    if (answerGrid) answerGrid.innerHTML = "";
    if (iconBank) iconBank.innerHTML = "";

    selectedIcon = null;
    const selectedDisplay = document.getElementById("selectedIcon");
    if (selectedDisplay) selectedDisplay.innerHTML = '<span class="text-muted small">None Selected</span>';

    buildAnswerGrid();
    buildIconBank();
}

function buildAnswerGrid() {
    for (let i = 0; i < 9; i++) {
        const cell = document.createElement("div");
        cell.className = "grid-cell";
        cell.dataset.position = i;
        answerGrid.appendChild(cell);
    }
}

function buildIconBank() {
    let icons = [...GAME_DATA[currentRound]];

    // Shuffle icons
    icons.sort(() => Math.random() - 0.5);

    icons.forEach(item => {
        const div = document.createElement("div");
        div.className = "icon-item";
        div.dataset.label = item.icon.label;
        div.innerHTML = `<i class="bi bi-${item.icon.id}"></i>`;

        div.onclick = function () {
            if (div.classList.contains("placed")) return;

            document.querySelectorAll(".icon-item").forEach(i => {
                i.classList.remove("selected");
            });

            div.classList.add("selected");
            selectedIcon = item;

            const selectedDisplay = document.getElementById("selectedIcon");
            if (selectedDisplay) {
                selectedDisplay.innerHTML = `
                    <i class="bi bi-${item.icon.id}"></i>
                    <span>${item.icon.label}</span>
                `;
            }
        };

        iconBank.appendChild(div);
    });

    enablePlacement();
}

function enablePlacement() {
    const cells = document.querySelectorAll("#answerGrid .grid-cell");

    cells.forEach(cell => {
        cell.onclick = function () {
            const pos = parseInt(cell.dataset.position);

            // If cell already has an item, click to remove/un-place it
            if (cell.innerHTML !== "") {
                for (const label in userPlacement) {
                    if (userPlacement[label] === pos) {
                        delete userPlacement[label];
                        document.querySelectorAll(".icon-item").forEach(icon => {
                            if (icon.dataset.label === label) {
                                icon.classList.remove("placed");
                                icon.classList.remove("selected");
                            }
                        });
                        break;
                    }
                }
                cell.innerHTML = "";
                selectedIcon = null;
                const selectedDisplay = document.getElementById("selectedIcon");
                if (selectedDisplay) selectedDisplay.innerHTML = '<span class="text-muted small">None Selected</span>';
                return;
            }

            // If no icon selected from inventory bank, return
            if (!selectedIcon) return;

            cell.innerHTML = `<i class="bi bi-${selectedIcon.icon.id}"></i>`;
            userPlacement[selectedIcon.icon.label] = pos;

            document.querySelectorAll(".icon-item").forEach(icon => {
                if (icon.dataset.label === selectedIcon.icon.label) {
                    icon.classList.add("placed");
                    icon.classList.remove("selected");
                }
            });

            selectedIcon = null;
            const selectedDisplay = document.getElementById("selectedIcon");
            if (selectedDisplay) selectedDisplay.innerHTML = '<span class="text-muted small">None Selected</span>';

            checkRoundComplete();
        };
    });
}

function checkRoundComplete() {
    const totalObjects = GAME_DATA[currentRound].length;
    if (Object.keys(userPlacement).length !== totalObjects) return;

    let correct = 0;
    for (const label in userPlacement) {
        if (userPlacement[label] === originalPositions[label]) {
            correct++;
        }
    }

    const roundMarks = [5, 8, 12];
    score += Math.round((correct / totalObjects) * roundMarks[currentRound]);

    currentRound++;

    if (currentRound < GAME_DATA.length) {
        startRound();
    } else {
        finishGame();
    }
}

function finishGame() {
    if (timerInterval) clearInterval(timerInterval);

    const gameArea = document.getElementById("gameArea");
    if (gameArea) gameArea.style.display = "none";
    if (recallArea) recallArea.classList.add("d-none");

    const resultScreen = document.getElementById("resultScreen");
    if (resultScreen) resultScreen.classList.remove("d-none");

    const finalScore = document.getElementById("finalScore");
    if (finalScore) finalScore.innerText = score;

    const feedbackEl = document.getElementById("feedback");
    if (feedbackEl) {
        if (score >= 22) feedbackEl.innerText = "🌟 Superior Spatial Memory";
        else if (score >= 16) feedbackEl.innerText = "✅ Solid Spatial Memory";
        else feedbackEl.innerText = "⚠ Moderate Spatial Location Precision";
    }

    // Save score to backend
    const token = getCsrfToken();
    fetch("/save-object-location/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": token
        },
        body: JSON.stringify({
            object_location_score: score
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Object location score saved:", data);
    })
    .catch(err => {
        console.error("Error saving object location score:", err);
    });
}

// Continue Button Click Handler (Navigates to Delayed Recall)
const continueBtn = document.getElementById("continueBtn");
if (continueBtn) {
    continueBtn.onclick = function () {
        const token = getCsrfToken();
        fetch("/save-object-location/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": token
            },
            body: JSON.stringify({
                object_location_score: score
            })
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = "/delayed-recall/";
        })
        .catch(err => {
            console.error("Error saving object location score:", err);
            window.location.href = "/delayed-recall/";
        });
    };
}
