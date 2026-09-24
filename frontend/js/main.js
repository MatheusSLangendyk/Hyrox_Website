console.log("Hyrox website loaded");

const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");

tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
        tabButtons.forEach((btn) => btn.classList.remove("active"));
        tabPanels.forEach((panel) => panel.classList.remove("active"));

        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
    });
});

// Show the HRV number fields only when the user says they have HRV data
const hasHrvData = document.getElementById("hasHrvData");
const hrvFields = document.getElementById("hrv-fields");

hasHrvData.addEventListener("change", () => {
    hrvFields.classList.toggle("hidden", hasHrvData.value !== "Yes");
});

// Show the menstrual cycle question only when the user selects Female
const gender = document.getElementById("gender");
const womenQuestion = document.getElementById("women-question");

gender.addEventListener("change", () => {
    womenQuestion.classList.toggle("hidden", gender.value !== "Known Menstrual Cycle");
});

// Handle the readiness form submission
const submitButton = document.getElementById("submit-btn");
const readiness_result = document.getElementById("readiness_result");

const alwaysRequiredFields = [
    "fatigue",
    "sleepHours",
    "sleepQuality",
    "soreness",
    "mentalState",
    "hasHrvData",
    "gender",
];

function allFieldsAnswered() {
    const requiredFields = [...alwaysRequiredFields];

    if (hasHrvData.value === "Yes") {
        requiredFields.push("monthlyHrv", "currentHrv");
    }

    if (gender.value === "Known Menstrual Cycle") {
        requiredFields.push("cyclePhase");
    }

    return requiredFields.every((id) => document.getElementById(id).value !== "");
}

function collectAnswers() {
    const answers = {};
    const fieldIds = [...alwaysRequiredFields];

    if (hasHrvData.value === "Yes") {
        fieldIds.push("monthlyHrv", "currentHrv");
    }

    if (gender.value === "Known Menstrual Cycle") {
        fieldIds.push("cyclePhase");
    }

    fieldIds.forEach((id) => {
        answers[id] = document.getElementById(id).value;
    });

    return answers;
}

submitButton.addEventListener("click", async () => {
    if (!allFieldsAnswered()) {
        readiness_result.textContent = "Please answer all fields.";
        return;
    }

    // Flask runs on its own port, separate from Live Server's port,
    // so the full address is needed instead of a relative path.
    const response = await fetch("http://127.0.0.1:5001/api/readiness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectAnswers()),
    });
    const data = await response.json();

    // response.ok is true for 2xx status codes and false for errors like 400,
    // so the backend's error message is shown instead of "null%".
    if (!response.ok) {
        readiness_result.textContent = `Error: ${data.error}`;
        return;
    }

    readiness_result.textContent = `Training Readiness: ${data.readiness}%`;
});
