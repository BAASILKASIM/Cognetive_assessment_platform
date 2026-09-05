// ======================================================
// Clock Drawing Test - Canvas & Submission Controller
// ======================================================

const canvas = document.getElementById("clockCanvas");
const ctx = canvas ? canvas.getContext("2d") : null;

const instructionCard = document.getElementById("instructionCard");
const startBtn = document.getElementById("startBtn");
const drawingArea = document.getElementById("drawingArea");
const submitClockBtn = document.getElementById("submitClockBtn");

const penBtn = document.getElementById("penBtn");
const eraserBtn = document.getElementById("eraserBtn");
const undoBtn = document.getElementById("undoBtn");
const clearBtn = document.getElementById("clearBtn");
const strokeBtns = document.querySelectorAll(".stroke-btn");

const loadingAnalysis = document.getElementById("loadingAnalysis");
const resultCard = document.getElementById("resultCard");
const clockScoreDisplay = document.getElementById("clockScoreDisplay");
const contourScoreDisplay = document.getElementById("contourScoreDisplay");
const numbersScoreDisplay = document.getElementById("numbersScoreDisplay");
const handsScoreDisplay = document.getElementById("handsScoreDisplay");
const clockFeedbackDisplay = document.getElementById("clockFeedbackDisplay");
const continueBtn = document.getElementById("continueBtn");

let isDrawing = false;
let currentMode = "pen"; // "pen" or "eraser"
let currentLineWidth = 4;
let historyStack = [];
const MAX_HISTORY = 25;

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Start Task Button Handler
if (startBtn) {
    startBtn.addEventListener("click", function () {
        if (instructionCard) instructionCard.style.display = "none";
        if (drawingArea) drawingArea.style.display = "block";
        initCanvas();
    });
}

function initCanvas() {
    if (!canvas || !ctx) return;

    // Set internal resolution for crisp rendering
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = 500 * dpr;
    canvas.height = 500 * dpr;
    ctx.scale(dpr, dpr);

    // Set background to pure white
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, 500, 500);

    // Initial drawing styles
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = currentLineWidth;

    saveHistoryState();
    attachCanvasEvents();
}

function saveHistoryState() {
    if (!ctx) return;
    if (historyStack.length >= MAX_HISTORY) {
        historyStack.shift();
    }
    historyStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
}

function getPointerPos(e) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = 500 / rect.width;
    const scaleY = 500 / rect.height;

    let clientX = e.clientX;
    let clientY = e.clientY;

    if (e.touches && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    }

    return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY
    };
}

function attachCanvasEvents() {
    // Mouse events
    canvas.addEventListener("mousedown", startDrawing);
    canvas.addEventListener("mousemove", draw);
    window.addEventListener("mouseup", stopDrawing);

    // Touch events for mobile / tablets
    canvas.addEventListener("touchstart", (e) => {
        e.preventDefault();
        startDrawing(e);
    }, { passive: false });

    canvas.addEventListener("touchmove", (e) => {
        e.preventDefault();
        draw(e);
    }, { passive: false });

    window.addEventListener("touchend", stopDrawing);
}

let lastPos = null;

function startDrawing(e) {
    isDrawing = true;
    const pos = getPointerPos(e);
    lastPos = pos;

    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);

    if (currentMode === "eraser") {
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = currentLineWidth * 3;
    } else {
        ctx.strokeStyle = "#000000";
        ctx.lineWidth = currentLineWidth;
    }
}

function draw(e) {
    if (!isDrawing || !lastPos) return;

    const pos = getPointerPos(e);

    ctx.beginPath();
    ctx.moveTo(lastPos.x, lastPos.y);
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();

    lastPos = pos;
}

function stopDrawing() {
    if (isDrawing) {
        isDrawing = false;
        lastPos = null;
        saveHistoryState();
    }
}

// Toolbar Handlers
const canvasWrapper = document.querySelector(".canvas-wrapper");

if (penBtn) {
    penBtn.addEventListener("click", () => {
        currentMode = "pen";
        penBtn.classList.add("active");
        if (eraserBtn) eraserBtn.classList.remove("active");
        if (canvasWrapper) canvasWrapper.classList.remove("eraser-mode");
    });
}

if (eraserBtn) {
    eraserBtn.addEventListener("click", () => {
        currentMode = "eraser";
        eraserBtn.classList.add("active");
        if (penBtn) penBtn.classList.remove("active");
        if (canvasWrapper) canvasWrapper.classList.add("eraser-mode");
    });
}

strokeBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        strokeBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentLineWidth = parseInt(btn.dataset.size || "4");
    });
});

if (undoBtn) {
    undoBtn.addEventListener("click", () => {
        if (historyStack.length > 1) {
            historyStack.pop(); // Remove current state
            const previousState = historyStack[historyStack.length - 1];
            ctx.putImageData(previousState, 0, 0);
        }
    });
}

if (clearBtn) {
    clearBtn.addEventListener("click", () => {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, 500, 500);
        saveHistoryState();
    });
}

// Validation: Check if user drew anything on the canvas
function isCanvasBlank() {
    const pixelBuffer = new Uint32Array(
        ctx.getImageData(0, 0, canvas.width, canvas.height).data.buffer
    );
    // Pure white is 0xFFFFFFFF in ABGR/RGBA
    const firstPixel = pixelBuffer[0];
    return !pixelBuffer.some(color => color !== firstPixel);
}

// Submit Drawing & Computer Vision Analysis
if (submitClockBtn) {
    submitClockBtn.addEventListener("click", () => {
        if (isCanvasBlank()) {
            alert("Please draw the clock on the canvas before submitting.");
            return;
        }

        const dataUrl = canvas.toDataURL("image/png");

        // Show loading state
        submitClockBtn.disabled = true;
        if (drawingArea) drawingArea.style.display = "none";
        if (loadingAnalysis) loadingAnalysis.style.display = "block";

        const csrftoken = getCookie("csrftoken");

        fetch("/save-clock-test/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({
                image_data: dataUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Clock Test CV Analysis:", data);

            if (loadingAnalysis) loadingAnalysis.style.display = "none";
            if (resultCard) resultCard.style.display = "block";

            const score = data.clock_score || 0;
            if (clockScoreDisplay) clockScoreDisplay.innerText = score;
            if (contourScoreDisplay) contourScoreDisplay.innerText = data.contour_score || 0;
            if (numbersScoreDisplay) numbersScoreDisplay.innerText = data.numbers_score || 0;
            if (handsScoreDisplay) handsScoreDisplay.innerText = data.hands_score || 0;

            if (clockFeedbackDisplay) {
                if (score >= 17) {
                    clockFeedbackDisplay.innerHTML = "🌟 Optimal Visuospatial & Executive Function";
                    clockFeedbackDisplay.className = "text-success fw-bold fs-5 mt-2";
                } else if (score >= 13) {
                    clockFeedbackDisplay.innerHTML = "✅ Normal Clock Drawing Performance";
                    clockFeedbackDisplay.className = "text-primary fw-bold fs-5 mt-2";
                } else if (score >= 9) {
                    clockFeedbackDisplay.innerHTML = "⚡ Mild Distortion in Hand / Number Placement";
                    clockFeedbackDisplay.className = "text-info fw-bold fs-5 mt-2";
                } else {
                    clockFeedbackDisplay.innerHTML = "⚠ Visuospatial Deviation Observed";
                    clockFeedbackDisplay.className = "text-warning fw-bold fs-5 mt-2";
                }
            }
        })
        .catch(err => {
            console.error("Error submitting clock drawing:", err);
            if (loadingAnalysis) loadingAnalysis.style.display = "none";
            if (drawingArea) drawingArea.style.display = "block";
            submitClockBtn.disabled = false;
            alert("An error occurred during analysis. Please try submitting again.");
        });
    });
}

// Continue Button
if (continueBtn) {
    continueBtn.addEventListener("click", () => {
        window.location.href = "/report/";
    });
}
