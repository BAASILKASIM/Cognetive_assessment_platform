// ==========================================
// Delayed Recall Memory Task & Score Combiner
// ==========================================

let currentQuestion = 0;
let delayedScore = 0;

const instructionCard = document.getElementById("instructionCard");
const questionScreen = document.getElementById("questionScreen");
const resultScreen = document.getElementById("resultScreen");

const startBtn = document.getElementById("startBtn");
const questionNumber = document.getElementById("questionNumber");
const questionText = document.getElementById("questionText");
const optionsContainer = document.getElementById("optionsContainer");

const finalTotalMemoryScore = document.getElementById("finalTotalMemoryScore");
const memoryFeedback = document.getElementById("memoryFeedback");
const breakdownVisual = document.getElementById("breakdownVisual");
const breakdownRecognition = document.getElementById("breakdownRecognition");
const breakdownLocation = document.getElementById("breakdownLocation");
const breakdownDelayed = document.getElementById("breakdownDelayed");
const continueBtn = document.getElementById("continueBtn");

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

// Start Task Button Handler
if (startBtn) {
    startBtn.addEventListener("click", startDelayedRecall);
}

function startDelayedRecall() {
    if (instructionCard) instructionCard.style.display = "none";
    if (questionScreen) questionScreen.style.display = "block";
    loadQuestion();
}

function loadQuestion() {
    if (currentQuestion >= QUESTIONS.length) {
        finishDelayedRecall();
        return;
    }

    const q = QUESTIONS[currentQuestion];
    if (questionNumber) questionNumber.innerHTML = `Question ${currentQuestion + 1} of ${QUESTIONS.length}`;
    if (questionText) questionText.innerHTML = q.question;
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

function checkAnswer(chosenLabel) {
    const q = QUESTIONS[currentQuestion];
    if (chosenLabel === q.answer) {
        delayedScore += 5;
    }

    currentQuestion++;
    loadQuestion();
}

function finishDelayedRecall() {
    if (questionScreen) questionScreen.style.display = "none";

    const token = getCsrfToken();

    fetch("/save-delayed-recall/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": token
        },
        body: JSON.stringify({
            delayed_recall_score: delayedScore
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Memory Assessment Aggregated:", data);

        const totalScore = (data.total_memory_score !== undefined) ? data.total_memory_score : (data.memory_score || 0);

        if (finalTotalMemoryScore) finalTotalMemoryScore.innerText = totalScore;
        if (breakdownVisual) breakdownVisual.innerText = (data.visual_memory_score !== undefined) ? data.visual_memory_score : 0;
        if (breakdownRecognition) breakdownRecognition.innerText = (data.recognition_score !== undefined) ? data.recognition_score : 0;
        if (breakdownLocation) breakdownLocation.innerText = (data.object_location_score !== undefined) ? data.object_location_score : 0;
        if (breakdownDelayed) breakdownDelayed.innerText = (data.delayed_recall_score !== undefined) ? data.delayed_recall_score : delayedScore;

        if (memoryFeedback) {
            if (totalScore >= 85) {
                memoryFeedback.innerHTML = "🌟 Exceptional Memory Retention";
                memoryFeedback.className = "text-success fw-bold fs-5 mt-2";
            } else if (totalScore >= 65) {
                memoryFeedback.innerHTML = "✅ Strong Memory Performance";
                memoryFeedback.className = "text-primary fw-bold fs-5 mt-2";
            } else if (totalScore >= 45) {
                memoryFeedback.innerHTML = "⚡ Moderate Memory Performance";
                memoryFeedback.className = "text-info fw-bold fs-5 mt-2";
            } else {
                memoryFeedback.innerHTML = "⚠ Memory Training Recommended";
                memoryFeedback.className = "text-warning fw-bold fs-5 mt-2";
            }
        }

        if (resultScreen) resultScreen.style.display = "block";
    })
    .catch(err => {
        console.error("Error saving delayed recall score:", err);
        if (resultScreen) resultScreen.style.display = "block";
    });
}

// Continue to next stage (Clock Test)
if (continueBtn) {
    continueBtn.addEventListener("click", function () {
        window.location.href = "/clock-test/";
    });
}
