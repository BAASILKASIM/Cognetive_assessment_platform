const memoryGrid = document.getElementById("memoryGrid");

const cells = [];

let pattern = [];
let selected = [];
let canClick = false;

let currentRound = 1;

const roundPatterns = [3, 5, 7];

const roundScores = [8, 10, 12];

let visualMemoryScore = 0;


// Create 9 cells
for (let i = 0; i < 9; i++) {

    const cell = document.createElement("div");

    cell.classList.add("memory-cell");

    cell.dataset.index = i;

    memoryGrid.appendChild(cell);

    cells.push(cell);

}


// Add click events
cells.forEach(cell => {

    cell.addEventListener("click", function () {

        if (!canClick) return;

        const index = Number(cell.dataset.index);

        // Deselect if already selected
        if (selected.includes(index)) {

            selected = selected.filter(i => i !== index);

            cell.classList.remove("selected");

        }

        // Select new cell
        else {

            // Don't allow selecting more cells than shown
            if (selected.length >= pattern.length) return;

            selected.push(index);

            cell.classList.add("selected");

        }

        // Automatically check answer
        if (selected.length === pattern.length) {

            canClick = false;

            setTimeout(checkAnswer, 500);

        }

    });

});


// Pick random cells
function generatePattern(count) {

    pattern = [];

    while (pattern.length < count) {

        let random = Math.floor(Math.random() * 9);

        if (!pattern.includes(random)) {

            pattern.push(random);

        }

    }

}


// Show pattern
function showPattern() {

    canClick = false;

    selected = [];

    // Clear previous selections
    cells.forEach(cell => {

        cell.classList.remove("selected");

    });

    pattern.forEach(index => {

        cells[index].classList.add("active");

    });

    setTimeout(() => {

        pattern.forEach(index => {

            cells[index].classList.remove("active");

        });

        canClick = true;

    }, 3000);

}


// Check answer
function checkAnswer() {

    const sortedPattern = [...pattern].sort();
    const sortedSelected = [...selected].sort();

    const correct =
        JSON.stringify(sortedPattern) === JSON.stringify(sortedSelected);

    if (correct) {

        visualMemoryScore += roundScores[currentRound - 1];

    }

    if (currentRound < 3) {

        currentRound++;

        document.getElementById("stepNumber").innerText = currentRound;

        setTimeout(startNextRound, 1200);

    }

    else {

        finishVisualMemory();

    }

}

function startNextRound() {

    selected = [];

    cells.forEach(cell => {

        cell.classList.remove("selected");

    });

    generatePattern(roundPatterns[currentRound - 1]);

    showPattern();

}


function finishVisualMemory() {

    if (typeof saveVisualMemoryScore === "function") {
        saveVisualMemoryScore(visualMemoryScore);
    }

}

// Start Game on button click
const startBtn = document.getElementById("startBtn");

if (startBtn) {
    startBtn.addEventListener("click", function () {
        const instructionCard = document.getElementById("instructionCard");
        if (instructionCard) instructionCard.style.display = "none";
        const gameArea = document.getElementById("gameArea");
        if (gameArea) gameArea.style.display = "block";
        generatePattern(roundPatterns[0]);
        showPattern();
    });
} else {
    generatePattern(roundPatterns[0]);
    showPattern();
}