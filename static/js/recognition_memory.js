// ======================
// Recognition Memory Test
// ======================

let timer = 10;
let currentQuestion = 0;
let score = 0;

const exposureScreen = document.getElementById("exposureScreen");
const questionScreen = document.getElementById("questionScreen");
const resultScreen = document.getElementById("resultScreen");
const timerText = document.getElementById("timer");

const questionNumber = document.getElementById("questionNumber");
const questionText = document.getElementById("questionText");
const optionsContainer = document.getElementById("optionsContainer");

const finalScore = document.getElementById("finalScore");
const feedback = document.getElementById("feedback");
const startBtn = document.getElementById("startBtn");

// Helper to get CSRF token reliably
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

// Start / Exposure Countdown
if (startBtn) {
    startBtn.addEventListener("click", startRecognitionTest);
}

function startRecognitionTest() {
    const instructionCard = document.getElementById("instructionCard");
    if (instructionCard) instructionCard.style.display = "none";
    if (exposureScreen) exposureScreen.style.display = "block";

    const countdown = setInterval(() => {
        timer--;
        if (timerText) timerText.innerText = timer;

        if (timer <= 0) {
            clearInterval(countdown);
            if (exposureScreen) exposureScreen.style.display = "none";
            if (questionScreen) questionScreen.style.display = "block";
            loadQuestion();
        }
    }, 1000);
}

// Load Question
function loadQuestion() {
    if (currentQuestion >= QUESTIONS.length) {
        finishTest();
        return;
    }

    const q = QUESTIONS[currentQuestion];

    if (questionNumber) {
        questionNumber.innerHTML = `Question ${currentQuestion + 1} of ${QUESTIONS.length}`;
    }

    if (questionText) {
        questionText.innerHTML = q.question;
    }

    if (optionsContainer) {
        optionsContainer.innerHTML = "";

        q.options.forEach(option => {
            const col = document.createElement("div");
            col.className = "col-6 col-md-3";

            col.innerHTML = `
                <div class="recognition-option-card">
                    <i class="bi bi-${option.id}"></i>
                    <h6>${option.label}</h6>
                </div>
            `;

            col.onclick = function () {
                checkAnswer(option.label);
            };

            optionsContainer.appendChild(col);
        });
    }
}

// Check Answer
function checkAnswer(answer) {
    const q = QUESTIONS[currentQuestion];
    if (answer === q.answer) {
        score += 5;
    }

    currentQuestion++;
    loadQuestion();
}

// Finish Test
function finishTest() {
    if (questionScreen) questionScreen.style.display = "none";
    if (resultScreen) resultScreen.style.display = "block";
    if (finalScore) finalScore.innerHTML = score;

    if (feedback) {
        if (score >= 20) {
            feedback.innerHTML = "🌟 Superior Item Recognition Memory";
            feedback.className = "text-success fw-bold mt-2";
        } else if (score >= 15) {
            feedback.innerHTML = "✅ Solid Item Recognition Memory";
            feedback.className = "text-primary fw-bold mt-2";
        } else {
            feedback.innerHTML = "⚠ Moderate Recognition Precision";
            feedback.className = "text-warning fw-bold mt-2";
        }
    }
}

// Continue Button Click Handler
const continueBtn = document.getElementById("continueBtn");
if (continueBtn) {
    continueBtn.onclick = function () {
        const token = getCsrfToken();

        fetch("/save-recognition-memory/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": token
            },
            body: JSON.stringify({
                recognition_score: score
            })
        })
        .then(response => response.json())
        .then(data => {
            window.location.href = "/object-location-memory/";
        })
        .catch(err => {
            console.error("Error saving recognition memory score:", err);
            // Fallback navigation so user is never stuck
            window.location.href = "/object-location-memory/";
        });
    };
}